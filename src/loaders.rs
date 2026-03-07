use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::Arc;

use cached::proc_macro::cached;
use encoding_rs::Encoding;
use pyo3::exceptions::PyUnicodeError;
use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;
use sugar_path::SugarPath;

use crate::template::django_rusty_templates::{Engine, Template};

static APPS: PyOnceLock<Py<PyAny>> = PyOnceLock::new();

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LoaderError {
    pub tried: Vec<(String, String)>,
}

fn abspath(path: &Path) -> Option<PathBuf> {
    match path.as_os_str().is_empty() {
        false => std::path::absolute(path).map(|p| p.normalize()).ok(),
        true => std::env::current_dir().ok(),
    }
}

fn safe_join(directory: &Path, template_name: &str) -> Option<PathBuf> {
    let final_path = abspath(&directory.join(template_name))?;
    let directory = abspath(directory)?;
    if final_path.starts_with(directory) {
        Some(final_path)
    } else {
        None
    }
}

fn get_app_template_dir(path: Bound<'_, PyAny>, dirname: &str) -> PyResult<Option<PathBuf>> {
    if path.is_truthy()? {
        let path_buf: PathBuf = path.extract()?;
        let template_path = path_buf.join(dirname);
        if template_path.is_dir() {
            return Ok(Some(template_path));
        }
    }
    Ok(None)
}

#[cached(
    size = 128,          // Cache size
    result = true,       // Cache Result type
    key = "String",      // Use owned String as key
    convert = r##"{ dirname.to_string() }"## // Convert &str to String
)]
fn get_app_template_dirs(py: Python<'_>, dirname: &str) -> PyResult<Vec<PathBuf>> {
    let apps = APPS.import(py, "django.apps", "apps")?;
    let app_configs = apps.call_method0("get_app_configs")?;

    let mut template_dirs = Vec::new();
    for app_config_result in app_configs.try_iter()? {
        let path = app_config_result?.getattr("path")?;
        if let Some(template_path) = get_app_template_dir(path, dirname)? {
            template_dirs.push(template_path);
        }
    }

    Ok(template_dirs)
}
#[derive(Debug)]
pub struct FileSystemLoader {
    dirs: Vec<PathBuf>,
    encoding: &'static Encoding,
}

impl FileSystemLoader {
    pub fn new(dirs: Vec<PathBuf>, encoding: &'static Encoding) -> Self {
        Self { dirs, encoding }
    }

    pub fn from_pathbuf(dirs: Vec<PathBuf>, encoding: &'static Encoding) -> Self {
        Self { dirs, encoding }
    }

    fn get_template(
        &self,
        py: Python<'_>,
        template_name: &str,
        engine: Arc<Engine>,
    ) -> Result<PyResult<Template>, LoaderError> {
        let mut tried = Vec::new();
        for template_dir in &self.dirs {
            let Some(path) = safe_join(template_dir, template_name) else {
                continue;
            };
            let Ok(bytes) = std::fs::read(&path) else {
                tried.push((
                    path.display().to_string(),
                    "Source does not exist".to_string(),
                ));
                continue;
            };
            let (contents, encoding, malformed) = self.encoding.decode(&bytes);
            if malformed {
                return Ok(Err(PyUnicodeError::new_err(format!(
                    "Could not open {} with {} encoding.",
                    path.display(),
                    encoding.name()
                ))));
            }
            return Ok(Template::new(py, &contents, path, template_name, engine));
        }
        Err(LoaderError { tried })
    }
}
#[derive(Debug)]
pub struct AppDirsLoader {
    encoding: &'static Encoding,
}

impl AppDirsLoader {
    pub fn new(encoding: &'static Encoding) -> Self {
        Self { encoding }
    }

    fn get_template(
        &self,
        py: Python<'_>,
        template_name: &str,
        engine: Arc<Engine>,
    ) -> Result<PyResult<Template>, LoaderError> {
        let dirs = match get_app_template_dirs(py, "templates") {
            Ok(dirs) => dirs,
            Err(e) => return Ok(Err(e)),
        };
        let filesystem_loader = FileSystemLoader::from_pathbuf(dirs, self.encoding);
        filesystem_loader.get_template(py, template_name, engine)
    }
}
#[derive(Debug)]
pub struct CachedLoader {
    cache: HashMap<String, Result<Template, LoaderError>>,
    pub loaders: Vec<Loader>,
}

impl CachedLoader {
    pub fn new(loaders: Vec<Loader>) -> Self {
        Self {
            loaders,
            cache: HashMap::new(),
        }
    }

    fn get_template(
        &mut self,
        py: Python<'_>,
        template_name: &str,
        engine: Arc<Engine>,
    ) -> Result<PyResult<Template>, LoaderError> {
        match self.cache.get(template_name) {
            Some(Ok(template)) => Ok(Ok((*template).clone())),
            Some(Err(e)) => Err(e.clone()),
            None => {
                let mut tried = Vec::new();
                for loader in &mut self.loaders {
                    match loader.get_template(py, template_name, engine.clone()) {
                        Ok(Ok(template)) => {
                            self.cache
                                .insert(template_name.to_string(), Ok(template.clone()));
                            return Ok(Ok(template));
                        }
                        Ok(Err(e)) => return Ok(Err(e)),
                        Err(mut e) => tried.append(&mut e.tried),
                    }
                }
                let error = LoaderError { tried };
                self.cache
                    .insert(template_name.to_string(), Err(error.clone()));
                Err(error)
            }
        }
    }
}
#[derive(Debug)]
pub struct LocMemLoader {
    templates: HashMap<String, String>,
}

impl LocMemLoader {
    #[allow(dead_code)]
    pub fn new(templates: HashMap<String, String>) -> Self {
        Self { templates }
    }

    fn get_template(
        &self,
        py: Python<'_>,
        template_name: &str,
        engine: Arc<Engine>,
    ) -> Result<PyResult<Template>, LoaderError> {
        if let Some(contents) = self.templates.get(template_name) {
            Ok(Template::new(
                py,
                contents,
                PathBuf::from(template_name),
                template_name,
                engine,
            ))
        } else {
            Err(LoaderError {
                tried: vec![(
                    template_name.to_string(),
                    "Source does not exist".to_string(),
                )],
            })
        }
    }
}
#[derive(Debug)]
pub struct ExternalLoader {}

impl ExternalLoader {
    fn get_template(
        &self,
        _py: Python<'_>,
        _template_name: &str,
        _engine: Arc<Engine>,
    ) -> Result<PyResult<Template>, LoaderError> {
        std::todo!() // Bail here because it does not make much sense to convert from PyErr to empty LoaderError
    }
}

#[derive(Debug)]
pub enum Loader {
    FileSystem(FileSystemLoader),
    AppDirs(AppDirsLoader),
    Cached(CachedLoader),
    #[allow(dead_code)]
    LocMem(LocMemLoader),
    #[allow(dead_code)]
    External(ExternalLoader),
}

impl Loader {
    pub fn get_template(
        &mut self,
        py: Python<'_>,
        template_name: &str,
        engine: Arc<Engine>,
    ) -> Result<PyResult<Template>, LoaderError> {
        match self {
            Self::FileSystem(loader) => loader.get_template(py, template_name, engine),
            Self::AppDirs(loader) => loader.get_template(py, template_name, engine),
            Self::Cached(loader) => loader.get_template(py, template_name, engine),
            Self::LocMem(loader) => loader.get_template(py, template_name, engine),
            Self::External(loader) => loader.get_template(py, template_name, engine),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::{BoundObject, IntoPyObjectExt};

    use proptest::prelude::*;

    fn setup_django(py: Python<'_>) {
        // Import the os module and set the DJANGO_SETTINGS_MODULE environment variable
        let os_module = PyModule::import(py, "os").unwrap();
        let environ = os_module.getattr("environ").unwrap();
        environ
            .call_method(
                "setdefault",
                ("DJANGO_SETTINGS_MODULE", "tests.settings"),
                None,
            )
            .unwrap();

        // Import the django module and call django.setup()
        let django_module = PyModule::import(py, "django").unwrap();
        django_module.call_method0("setup").unwrap();
    }

    #[test]
    fn test_filesystem_loader() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let loader =
                FileSystemLoader::new(vec![PathBuf::from("tests/templates")], encoding_rs::UTF_8);
            let template = loader
                .get_template(py, "basic.txt", engine)
                .unwrap()
                .unwrap();

            let mut expected = std::env::current_dir().unwrap();
            #[cfg(not(windows))]
            expected.push("tests/templates/basic.txt");
            #[cfg(windows)]
            expected.push("tests\\templates\\basic.txt");
            assert_eq!(template.filename.unwrap(), expected);
        });
    }

    #[test]
    fn test_filesystem_loader_missing_template() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let loader =
                FileSystemLoader::new(vec![PathBuf::from("tests/templates")], encoding_rs::UTF_8);
            let error = loader.get_template(py, "missing.txt", engine).unwrap_err();

            let mut expected = std::env::current_dir().unwrap();
            #[cfg(not(windows))]
            expected.push("tests/templates/missing.txt");
            #[cfg(windows)]
            expected.push("tests\\templates\\missing.txt");
            assert_eq!(
                error,
                LoaderError {
                    tried: vec![(
                        expected.display().to_string(),
                        "Source does not exist".to_string(),
                    )],
                },
            );
        });
    }

    #[test]
    fn test_filesystem_loader_invalid_encoding() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let loader =
                FileSystemLoader::new(vec![PathBuf::from("tests/templates")], encoding_rs::UTF_8);
            let error = loader
                .get_template(py, "invalid.txt", engine)
                .unwrap()
                .unwrap_err();

            let mut expected = std::env::current_dir().unwrap();
            #[cfg(not(windows))]
            expected.push("tests/templates/invalid.txt");
            #[cfg(windows)]
            expected.push("tests\\templates\\invalid.txt");
            assert_eq!(
                error.to_string(),
                format!(
                    "UnicodeError: Could not open {} with UTF-8 encoding.",
                    expected.display()
                )
            );
        });
    }

    #[test]
    fn test_cached_loader() {
        Python::initialize();

        Python::attach(|py| {
            // Helper to check cache contents
            let verify_cache = |cache: &HashMap<String, Result<Template, LoaderError>>,
                                key: &str,
                                expected_path: &Path| {
                if let Some(Ok(cached_template)) = cache.get(key) {
                    assert_eq!(cached_template.filename.as_ref().unwrap(), expected_path);
                } else {
                    panic!("Expected '{key}' to be in cache.");
                }
            };

            let engine = Arc::new(Engine::empty());

            // Create a FileSystemLoader for the CachedLoader
            let filesystem_loader =
                FileSystemLoader::new(vec![PathBuf::from("tests/templates")], encoding_rs::UTF_8);

            // Wrap the FileSystemLoader in a CachedLoader
            let mut cached_loader = CachedLoader::new(vec![Loader::FileSystem(filesystem_loader)]);

            // Load a template via the CachedLoader
            let template = cached_loader
                .get_template(py, "basic.txt", engine.clone())
                .expect("Failed to load template")
                .expect("Template file could not be read");

            // Verify the template filename
            let mut expected_path =
                std::env::current_dir().expect("Failed to get current directory");
            #[cfg(not(windows))]
            expected_path.push("tests/templates/basic.txt");
            #[cfg(windows)]
            expected_path.push("tests\\templates\\basic.txt");
            assert_eq!(template.filename.unwrap(), expected_path);

            // Verify the cache state after first load
            assert_eq!(cached_loader.cache.len(), 1);
            verify_cache(&cached_loader.cache, "basic.txt", &expected_path);

            // Load the same template again via the CachedLoader
            let template = cached_loader
                .get_template(py, "basic.txt", engine)
                .expect("Failed to load template")
                .expect("Template file could not be read");

            // Verify the template filename again
            assert_eq!(template.filename.unwrap(), expected_path);

            // Verify the cache state remains consistent
            assert_eq!(cached_loader.cache.len(), 1);
            verify_cache(&cached_loader.cache, "basic.txt", &expected_path);
        });
    }

    #[test]
    fn test_cached_loader_missing_template() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let filesystem_loader =
                FileSystemLoader::new(vec![PathBuf::from("tests/templates")], encoding_rs::UTF_8);

            let mut cached_loader = CachedLoader::new(vec![Loader::FileSystem(filesystem_loader)]);
            let error = cached_loader
                .get_template(py, "missing.txt", engine.clone())
                .unwrap_err();

            let mut expected = std::env::current_dir().unwrap();
            #[cfg(not(windows))]
            expected.push("tests/templates/missing.txt");
            #[cfg(windows)]
            expected.push("tests\\templates\\missing.txt");
            let expected_err = LoaderError {
                tried: vec![(
                    expected.display().to_string(),
                    "Source does not exist".to_string(),
                )],
            };
            assert_eq!(error, expected_err);

            let cache = &cached_loader.cache;
            assert_eq!(
                cache.get("missing.txt").unwrap().as_ref().unwrap_err(),
                &expected_err
            );

            let error = cached_loader
                .get_template(py, "missing.txt", engine)
                .unwrap_err();
            assert_eq!(error, expected_err);
        });
    }

    #[test]
    fn test_cached_loader_invalid_encoding() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let filesystem_loader =
                FileSystemLoader::new(vec![PathBuf::from("tests/templates")], encoding_rs::UTF_8);

            let mut cached_loader = CachedLoader::new(vec![Loader::FileSystem(filesystem_loader)]);
            let error = cached_loader
                .get_template(py, "invalid.txt", engine)
                .unwrap()
                .unwrap_err();

            let mut expected = std::env::current_dir().unwrap();
            #[cfg(not(windows))]
            expected.push("tests/templates/invalid.txt");
            #[cfg(windows)]
            expected.push("tests\\templates\\invalid.txt");
            assert_eq!(
                error.to_string(),
                format!(
                    "UnicodeError: Could not open {} with UTF-8 encoding.",
                    expected.display()
                )
            );
        });
    }

    #[test]
    fn test_locmem_loader() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let mut templates: HashMap<String, String> = HashMap::new();
            templates.insert("index.html".to_string(), "index".to_string());

            let loader = LocMemLoader::new(templates);

            let template = loader
                .get_template(py, "index.html", engine)
                .unwrap()
                .unwrap();
            assert_eq!(template.template, "index".to_string().into());
            assert_eq!(template.filename.unwrap(), PathBuf::from("index.html"));
        });
    }

    #[test]
    fn test_locmem_loader_missing_template() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Arc::new(Engine::empty());
            let templates: HashMap<String, String> = HashMap::new();

            let loader = LocMemLoader::new(templates);

            let error = loader.get_template(py, "index.html", engine).unwrap_err();
            assert_eq!(
                error,
                LoaderError {
                    tried: vec![(
                        "index.html".to_string(),
                        "Source does not exist".to_string(),
                    )],
                },
            );
        });
    }

    #[test]
    fn test_appdirs_loader() {
        Python::initialize();

        Python::attach(|py| {
            // Setup Django
            setup_django(py);

            let engine = Arc::new(Engine::empty());
            let loader = AppDirsLoader::new(encoding_rs::UTF_8);
            let template = loader
                .get_template(py, "basic.txt", engine)
                .unwrap()
                .unwrap();

            let mut expected = std::env::current_dir().unwrap();
            #[cfg(not(windows))]
            expected.push("tests/templates/basic.txt");
            #[cfg(windows)]
            expected.push("tests\\templates\\basic.txt");
            assert_eq!(template.filename.unwrap(), expected);
        });
    }

    #[test]
    fn test_appdirs_loader_missing_template() {
        Python::initialize();

        Python::attach(|py| {
            // Setup Django
            setup_django(py);

            let engine = Arc::new(Engine::empty());
            let loader = AppDirsLoader::new(encoding_rs::UTF_8);
            let error = loader.get_template(py, "missing.txt", engine).unwrap_err();

            let mut expected = std::env::current_dir().unwrap();
            #[cfg(not(windows))]
            expected.push("tests/templates/missing.txt");
            #[cfg(windows)]
            expected.push("tests\\templates\\missing.txt");

            let auth = py.import("django.contrib.auth").unwrap();
            let auth: PathBuf = auth.getattr("__file__").unwrap().extract().unwrap();
            let mut auth = auth.parent().unwrap().to_path_buf();
            #[cfg(not(windows))]
            auth.push("templates/missing.txt");
            #[cfg(windows)]
            auth.push("templates\\missing.txt");

            assert_eq!(
                error,
                LoaderError {
                    tried: vec![
                        (
                            expected.display().to_string(),
                            "Source does not exist".to_string(),
                        ),
                        (
                            auth.display().to_string(),
                            "Source does not exist".to_string(),
                        ),
                    ],
                },
            );
        });
    }

    #[test]
    fn test_appdirs_loader_invalid_encoding() {
        Python::initialize();

        Python::attach(|py| {
            // Setup Django
            setup_django(py);

            let engine = Arc::new(Engine::empty());
            let loader = AppDirsLoader::new(encoding_rs::UTF_8);
            let error = loader
                .get_template(py, "invalid.txt", engine)
                .unwrap()
                .unwrap_err();

            let mut expected = std::env::current_dir().unwrap();
            #[cfg(not(windows))]
            expected.push("tests/templates/invalid.txt");
            #[cfg(windows)]
            expected.push("tests\\templates\\invalid.txt");
            assert_eq!(
                error.to_string(),
                format!(
                    "UnicodeError: Could not open {} with UTF-8 encoding.",
                    expected.display()
                )
            );
        });
    }

    #[test]
    fn test_get_app_template_dir_special_cases() {
        Python::initialize();

        Python::attach(|py| {
            // Test with None path
            let none_path = py.None().into_bound(py);
            let result = get_app_template_dir(none_path, "templates");
            assert!(result.is_ok());
            assert_eq!(result.unwrap(), None);

            // Test with invalid type (integer)
            let invalid = 42.into_bound_py_any(py).unwrap();
            let result = get_app_template_dir(invalid, "templates");
            assert!(result.is_err());
        });
    }

    #[test]
    fn test_get_app_template_dir_with_str() {
        Python::initialize();

        Python::attach(|py| {
            // Test with Python string for current directory (nonexistent template)
            let current_dir = ".".into_bound_py_any(py).unwrap();
            let result = get_app_template_dir(current_dir, "nonexistent");
            assert!(result.is_ok());
            assert_eq!(result.unwrap(), None);

            // Test with Python string for the "tests" directory
            let tests_dir = "tests".into_bound_py_any(py).unwrap();
            let result = get_app_template_dir(tests_dir, "templates");
            assert!(result.is_ok());
            let expected_path = PathBuf::from("tests").join("templates");
            assert_eq!(result.unwrap(), Some(expected_path));
        });
    }

    #[test]
    fn test_get_app_template_dir_with_pathlib() {
        Python::initialize();

        Python::attach(|py| {
            // Import pathlib.Path
            let path_module = py.import("pathlib").unwrap();
            let path_cls = path_module.getattr("Path").unwrap();

            // Test with pathlib.Path for current directory (nonexistent template)
            let path_obj = path_cls.call1((".",)).unwrap().into_bound();
            let result = get_app_template_dir(path_obj, "nonexistent");
            assert!(result.is_ok());
            assert_eq!(result.unwrap(), None);

            // Test with pathlib.Path for the "tests" directory
            let path_obj = path_cls.call1(("tests",)).unwrap().into_bound();
            let result = get_app_template_dir(path_obj, "templates");
            assert!(result.is_ok());
            let expected_path = PathBuf::from("tests").join("templates");
            assert_eq!(result.unwrap(), Some(expected_path));
        });
    }

    #[test]
    fn test_get_app_template_dirs() {
        Python::initialize();

        Python::attach(|py| {
            // Setup Django
            setup_django(py);

            let dirs = get_app_template_dirs(py, "templates").unwrap();
            assert_eq!(dirs.len(), 2);

            let mut expected = std::env::current_dir().unwrap();
            expected.push("tests/templates");
            assert_eq!(dirs[0], expected);
        });
    }

    #[test]
    fn test_safe_join_absolute() {
        let path = PathBuf::from("/abc/");
        let joined = safe_join(&path, "def").unwrap();
        #[cfg(not(windows))]
        assert_eq!(joined, PathBuf::from("/abc/def"));
        #[cfg(windows)]
        assert!(joined.ends_with("\\abc\\def"));
    }

    #[test]
    fn test_safe_join_relative() {
        let path = PathBuf::from("abc");
        let joined = safe_join(&path, "def").unwrap();
        let mut expected = std::env::current_dir().unwrap();
        expected.push("abc/def");
        assert_eq!(joined, expected);
    }

    #[test]
    fn test_safe_join_absolute_starts_with_sep() {
        let path = PathBuf::from("/abc/");
        let joined = safe_join(&path, "/def");
        assert_eq!(joined, None);
    }

    #[test]
    fn test_safe_join_relative_starts_with_sep() {
        let path = PathBuf::from("abc");
        let joined = safe_join(&path, "/def");
        assert_eq!(joined, None);
    }

    #[test]
    fn test_safe_join_absolute_parent() {
        let path = PathBuf::from("/abc/");
        let joined = safe_join(&path, "../def");
        assert_eq!(joined, None);
    }

    #[test]
    fn test_safe_join_relative_parent() {
        let path = PathBuf::from("abc");
        let joined = safe_join(&path, "../def");
        assert_eq!(joined, None);
    }

    #[test]
    fn test_safe_join_absolute_parent_starts_with_sep() {
        let path = PathBuf::from("/abc/");
        let joined = safe_join(&path, "/../def");
        assert_eq!(joined, None);
    }

    #[test]
    fn test_safe_join_relative_parent_starts_with_sep() {
        let path = PathBuf::from("abc");
        let joined = safe_join(&path, "/../def");
        assert_eq!(joined, None);
    }

    #[test]
    fn test_safe_join_django_example() {
        let path = PathBuf::from("/dir");
        let joined = safe_join(&path, "/../d");
        assert_eq!(joined, None);
    }

    #[test]
    fn test_safe_join_django_example_variant() {
        let path = PathBuf::from("/dir");
        let joined = safe_join(&path, "/../directory");
        assert_eq!(joined, None);
    }

    #[test]
    fn test_safe_join_empty_path() {
        let path = PathBuf::from("");
        let joined = safe_join(&path, "directory").unwrap();
        let mut expected = std::env::current_dir().unwrap();
        expected.push("directory");
        assert_eq!(joined, expected);
    }

    #[test]
    fn test_safe_join_empty_path_and_template_name() {
        let path = PathBuf::from("");
        let joined = safe_join(&path, "").unwrap();
        let expected = std::env::current_dir().unwrap();
        assert_eq!(joined, expected);
    }

    #[test]
    fn test_safe_join_parent_and_empty_template_name() {
        let path = PathBuf::from("..");
        let joined = safe_join(&path, "").unwrap();
        let mut expected = std::env::current_dir().unwrap();
        expected.push("..");
        assert_eq!(joined, expected.normalize());
    }

    #[test]
    #[cfg_attr(
        windows,
        ignore = "Skipping on Windows due to path character restrictions"
    )]
    fn test_safe_join_matches_django_safe_join() {
        Python::initialize();
        proptest!(|(path: PathBuf, template_name: String)| {
            Python::attach(|py| {
                let utils_os = PyModule::import(py, "django.utils._os").unwrap();
                let django_safe_join = utils_os.getattr("safe_join").unwrap();

                let joined = django_safe_join
                    .call1((&path, &template_name))
                    .map(|joined| joined.extract::<PathBuf>().unwrap_or_default())
                    .ok();
                prop_assert_eq!(joined, safe_join(&path, &template_name));
                Ok(())
            })?;
        });
    }
}
