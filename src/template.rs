use pyo3::prelude::*;

#[pymodule]
pub mod django_rusty_templates {
    use std::collections::HashMap;
    use std::path::PathBuf;

    use encoding_rs::Encoding;
    use pyo3::exceptions::{PyAttributeError, PyImportError, PyOverflowError, PyValueError};
    use pyo3::import_exception;
    use pyo3::intern;
    use pyo3::prelude::*;
    use pyo3::types::{PyBool, PyDict, PyIterator, PyList, PyString, PyTuple};

    use crate::error::RenderError;
    use crate::loaders::{AppDirsLoader, CachedLoader, FileSystemLoader, Loader, LocMemLoader};
    use crate::parse::{Parser, TokenTree};
    use crate::render::Render;
    use crate::render::types::Context;
    use crate::types::TemplateString;
    use crate::utils::PyResultMethods;

    import_exception!(django.core.exceptions, ImproperlyConfigured);
    import_exception!(django.template.base, VariableDoesNotExist);
    import_exception!(django.template.exceptions, TemplateDoesNotExist);
    import_exception!(django.template.exceptions, TemplateSyntaxError);
    import_exception!(django.template.library, InvalidTemplateLibrary);
    import_exception!(django.urls, NoReverseMatch);

    trait WithSourceCode {
        fn with_source_code(
            err: miette::Report,
            source: impl miette::SourceCode + 'static,
        ) -> PyErr;
    }

    impl WithSourceCode for TemplateSyntaxError {
        fn with_source_code(
            err: miette::Report,
            source: impl miette::SourceCode + 'static,
        ) -> PyErr {
            let miette_err = err.with_source_code(source);
            Self::new_err(format!("{miette_err:?}"))
        }
    }

    impl WithSourceCode for VariableDoesNotExist {
        fn with_source_code(
            err: miette::Report,
            source: impl miette::SourceCode + 'static,
        ) -> PyErr {
            let miette_err = err.with_source_code(source);
            let report = format!("{miette_err:?}");
            // Work around old-style Python formatting in VariableDoesNotExist.__str__
            let report = report.replace("%", "%%");
            Self::new_err(report)
        }
    }

    impl WithSourceCode for PyOverflowError {
        fn with_source_code(
            err: miette::Report,
            source: impl miette::SourceCode + 'static,
        ) -> PyErr {
            let miette_err = err.with_source_code(source);
            Self::new_err(format!("{miette_err:?}"))
        }
    }

    impl WithSourceCode for PyValueError {
        fn with_source_code(
            err: miette::Report,
            source: impl miette::SourceCode + 'static,
        ) -> PyErr {
            let miette_err = err.with_source_code(source);
            Self::new_err(format!("{miette_err:?}"))
        }
    }

    #[derive(Debug)]
    pub struct EngineData {
        autoescape: bool,
        libraries: HashMap<String, Py<PyAny>>,
    }

    impl EngineData {
        #[cfg(test)]
        pub fn empty() -> Self {
            Self {
                autoescape: false,
                libraries: HashMap::new(),
            }
        }
    }

    fn import_libraries(libraries: Bound<'_, PyAny>) -> PyResult<HashMap<String, Py<PyAny>>> {
        let py = libraries.py();
        let libraries: HashMap<String, String> = libraries.extract()?;
        let mut libs = HashMap::with_capacity(libraries.len());
        for (name, path) in libraries {
            let library = match py.import(&path).ok_or_isinstance_of::<PyImportError>(py)? {
                Ok(library) => library,
                Err(e) => {
                    let error = format!(
                        "Invalid template library specified. ImportError raised when trying to load '{}': {}",
                        path,
                        e.value(py)
                    );
                    return Err(InvalidTemplateLibrary::new_err(error));
                }
            };
            let Ok(library) = library
                .getattr(intern!(py, "register"))
                .ok_or_isinstance_of::<PyAttributeError>(py)?
            else {
                let error = format!("Module '{path}' does not have a variable named 'register'");
                return Err(InvalidTemplateLibrary::new_err(error));
            };
            libs.insert(name, library.unbind());
        }
        Ok(libs)
    }

    /// Helper function to unpack a loader tuple configuration.
    /// See https://docs.djangoproject.com/en/stable/ref/templates/api/#django.template.Engine
    fn unpack<'py>(loader: &Bound<'py, PyAny>) -> PyResult<(String, Bound<'py, PyAny>)> {
        let mut items = loader.try_iter()?;
        let first_item = match items.next() {
            Some(item) => item?,
            None => return Err(ImproperlyConfigured::new_err("Configuration is empty")),
        };
        let loader_path = first_item.extract::<String>().map_err(|_| {
            ImproperlyConfigured::new_err(
                "First element of tuple configuration must be a Loader class name",
            )
        })?;
        let remaining_args = match items.next() {
            Some(item) => item?,
            None => {
                return Err(ImproperlyConfigured::new_err(
                    "Missing second element in tuple configuration",
                ));
            }
        };
        Ok((loader_path, remaining_args))
    }
    fn get_template_loaders<'py>(
        py: Python<'py>,
        template_loaders: Bound<'_, PyIterator>,
        encoding: &'static Encoding,
    ) -> PyResult<Vec<Loader>> {
        template_loaders
            .map(|template_loader| {
                template_loader
                    .and_then(|template_loader| find_template_loader(py, template_loader, encoding))
            })
            .collect()
    }

    fn find_template_loader<'py>(
        py: Python<'py>,
        loader: Bound<'_, PyAny>,
        encoding: &'static Encoding,
    ) -> PyResult<Loader> {
        if let Ok(loader_str) = loader.extract::<String>() {
            return map_loader(py, &loader_str, None, encoding);
        }

        let (loader_path, args) = unpack(&loader).map_err(|e| {
            ImproperlyConfigured::new_err(format!(
                "Invalid template loader: {loader}. {}",
                e.value(py),
            ))
        })?;

        map_loader(py, &loader_path, Some(args), encoding)
    }

    fn map_loader(
        py: Python<'_>,
        loader_path: &str,
        args: Option<Bound<'_, PyAny>>,
        encoding: &'static Encoding,
    ) -> PyResult<Loader> {
        match loader_path {
            "django.template.loaders.filesystem.Loader" => {
                let paths = args
                    .map(|arg| {
                        arg.try_iter()?
                            .map(|item| item?.extract::<PathBuf>())
                            .collect::<PyResult<Vec<_>>>()
                    })
                    .transpose()?
                    .unwrap_or_default();

                Ok(Loader::FileSystem(FileSystemLoader::new(paths, encoding)))
            }
            "django.template.loaders.app_directories.Loader" => {
                Ok(Loader::AppDirs(AppDirsLoader::new(encoding)))
            }
            "django.template.loaders.locmem.Loader" => {
                let templates = args
                    .map(|arg| arg.extract())
                    .transpose()?
                    .unwrap_or_default();

                Ok(Loader::LocMem(LocMemLoader::new(templates)))
            }
            "django.template.loaders.cached.Loader" => {
                let nested_loaders = args
                    .ok_or_else(|| {
                        ImproperlyConfigured::new_err(
                            "django.template.loaders.cached.Loader requires a list/tuple of loaders"
                        )
                    })?
                    .try_iter()?
                    .map(|inner_loader| find_template_loader(py, inner_loader?, encoding))
                    .collect::<PyResult<Vec<_>>>()?;

                Ok(Loader::Cached(CachedLoader::new(nested_loaders)))
            }
            // TODO: Return an `ExternalLoader` when it's fully implemented
            unknown => Err(ImproperlyConfigured::new_err(format!(
                "Invalid template loader class: {}",
                unknown
            ))),
        }
    }

    #[derive(Debug)]
    #[pyclass]
    pub struct Engine {
        #[allow(dead_code)]
        dirs: Vec<PathBuf>,
        #[pyo3(get)]
        app_dirs: bool,
        #[pyo3(get)]
        context_processors: Vec<String>,
        #[pyo3(get)]
        debug: bool,
        template_loaders: Vec<Loader>,
        #[pyo3(get)]
        string_if_invalid: String,
        #[allow(dead_code)]
        encoding: &'static Encoding,
        #[pyo3(get)]
        builtins: Vec<String>,
        data: EngineData,
    }

    #[pymethods]
    impl Engine {
        #[new]
        #[pyo3(signature = (dirs=None, app_dirs=false, context_processors=None, debug=false, loaders=None, string_if_invalid="".to_string(), file_charset="utf-8".to_string(), libraries=None, builtins=None, autoescape=true))]
        #[allow(clippy::too_many_arguments)] // We're matching Django's Engine __init__ signature
        pub fn new(
            py: Python<'_>,
            dirs: Option<Bound<'_, PyAny>>,
            app_dirs: bool,
            context_processors: Option<Bound<'_, PyAny>>,
            debug: bool,
            loaders: Option<Bound<'_, PyAny>>,
            string_if_invalid: String,
            file_charset: String,
            libraries: Option<Bound<'_, PyAny>>,
            #[allow(unused_variables)] builtins: Option<Bound<'_, PyAny>>,
            autoescape: bool,
        ) -> PyResult<Self> {
            let dirs = match dirs {
                Some(dirs) => dirs.extract()?,
                None => Vec::new(),
            };
            let context_processors = match context_processors {
                Some(context_processors) => context_processors.extract()?,
                None => Vec::new(),
            };
            let encoding = match Encoding::for_label(file_charset.as_bytes()) {
                Some(encoding) => encoding,
                None => {
                    return Err(PyValueError::new_err(format!(
                        "Unknown encoding: '{file_charset}'"
                    )));
                }
            };
            let template_loaders = match loaders {
                Some(_) if app_dirs => {
                    let err = ImproperlyConfigured::new_err(
                        "app_dirs must not be set when loaders is defined.",
                    );
                    return Err(err);
                }
                Some(loaders) => get_template_loaders(py, loaders.try_iter()?, encoding)?,
                None => {
                    let filesystem_loader =
                        Loader::FileSystem(FileSystemLoader::new(dirs.clone(), encoding));
                    let appdirs_loader = Loader::AppDirs(AppDirsLoader::new(encoding));
                    let loaders = if app_dirs {
                        vec![filesystem_loader, appdirs_loader]
                    } else {
                        vec![filesystem_loader]
                    };
                    let cached_loader = Loader::Cached(CachedLoader::new(loaders));
                    vec![cached_loader]
                }
            };
            let libraries = match libraries {
                None => HashMap::new(),
                Some(libraries) => import_libraries(libraries)?,
            };
            let builtins = vec![];
            let data = EngineData {
                autoescape,
                libraries,
            };
            Ok(Self {
                dirs,
                app_dirs,
                context_processors,
                debug,
                template_loaders,
                string_if_invalid,
                encoding,
                builtins,
                data,
            })
        }

        /// Return a compiled Template object for the given template name,
        /// handling template inheritance recursively.
        ///
        /// See https://docs.djangoproject.com/en/stable/ref/templates/api/#django.template.Engine.get_template
        pub fn get_template(
            &mut self,
            py: Python<'_>,
            template_name: String,
        ) -> PyResult<Template> {
            let mut tried = Vec::new();
            for loader in &mut self.template_loaders {
                match loader.get_template(py, &template_name, &self.data) {
                    Ok(template) => return template,
                    Err(e) => tried.push(e.tried),
                }
            }
            Err(TemplateDoesNotExist::new_err((template_name, tried)))
        }

        /// Given a list of template names, return the first that can be loaded.
        ///
        /// See https://docs.djangoproject.com/en/stable/ref/templates/api/#django.template.Engine.select_template
        pub fn select_template(
            &mut self,
            py: Python<'_>,
            template_name_list: Vec<String>,
        ) -> PyResult<Template> {
            if template_name_list.is_empty() {
                return Err(TemplateDoesNotExist::new_err("No template names provided"));
            }
            let mut not_found = Vec::new();
            for template_name in template_name_list {
                match self.get_template(py, template_name) {
                    Ok(template) => return Ok(template),
                    Err(e) if e.is_instance_of::<TemplateDoesNotExist>(py) => {
                        not_found.push(e.value(py).to_string())
                    }
                    Err(e) => return Err(e),
                }
            }
            Err(TemplateDoesNotExist::new_err(not_found.join(", ")))
        }

        #[allow(clippy::wrong_self_convention)] // We're implementing a Django interface
        pub fn from_string(&self, template_code: Bound<'_, PyString>) -> PyResult<Template> {
            Template::new_from_string(template_code.py(), template_code.extract()?, &self.data)
        }

        /// Render the template specified by template_name with the given context.
        /// For use in Django's test suite.
        #[pyo3(signature = (template_name, context=None))]
        pub fn render_to_string(
            &mut self,
            py: Python<'_>,
            template_name: Bound<'_, PyAny>,
            context: Option<Bound<'_, PyDict>>,
        ) -> PyResult<String> {
            let template = if template_name.is_instance_of::<PyList>()
                || template_name.is_instance_of::<PyTuple>()
            {
                self.select_template(py, template_name.extract()?)?
            } else {
                self.get_template(py, template_name.extract()?)?
            };

            template.render(py, context, None)
        }

        #[getter]
        pub fn dirs(&self) -> Vec<String> {
            self.dirs
                .iter()
                .map(|p| p.to_string_lossy().to_string())
                .collect()
        }
        #[getter]
        pub fn file_charset(&self) -> String {
            self.encoding.name().to_string()
        }

        #[getter]
        pub fn libraries<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
            let dict = PyDict::new(py);
            for (key, value) in &self.data.libraries {
                dict.set_item(key, value.bind(py))?;
            }
            Ok(dict)
        }

        #[getter]
        pub fn autoescape(&self) -> bool {
            self.data.autoescape
        }
    }

    #[derive(Debug, Clone, PartialEq)]
    #[pyclass]
    pub struct Template {
        pub filename: Option<PathBuf>,
        pub template: String,
        pub nodes: Vec<TokenTree>,
        pub autoescape: bool,
    }

    impl Template {
        pub fn new(
            py: Python<'_>,
            template: &str,
            filename: PathBuf,
            engine_data: &EngineData,
        ) -> PyResult<Self> {
            let mut parser = Parser::new(py, TemplateString(template), &engine_data.libraries);
            let nodes = match parser.parse() {
                Ok(nodes) => nodes,
                Err(err) => {
                    let err = err.try_into_parse_error()?;
                    let source =
                        miette::NamedSource::new(filename.to_string_lossy(), template.to_string());
                    return Err(TemplateSyntaxError::with_source_code(err.into(), source));
                }
            };
            Ok(Self {
                template: template.to_string(),
                filename: Some(filename),
                nodes,
                autoescape: engine_data.autoescape,
            })
        }

        pub fn new_from_string(
            py: Python<'_>,
            template: String,
            engine_data: &EngineData,
        ) -> PyResult<Self> {
            let mut parser = Parser::new(py, TemplateString(&template), &engine_data.libraries);
            let nodes = match parser.parse() {
                Ok(nodes) => nodes,
                Err(err) => {
                    let err = err.try_into_parse_error()?;
                    return Err(TemplateSyntaxError::with_source_code(err.into(), template));
                }
            };
            Ok(Self {
                template,
                filename: None,
                nodes,
                autoescape: engine_data.autoescape,
            })
        }

        fn _render(&self, py: Python<'_>, context: &mut Context) -> PyResult<String> {
            let mut rendered = String::with_capacity(self.template.len());
            let template = TemplateString(&self.template);
            for node in &self.nodes {
                match node.render(py, template, context) {
                    Ok(content) => rendered.push_str(&content),
                    Err(err) => {
                        let err = err.try_into_render_error()?;
                        match err {
                            RenderError::VariableDoesNotExist { .. }
                            | RenderError::ArgumentDoesNotExist { .. } => {
                                return Err(VariableDoesNotExist::with_source_code(
                                    err.into(),
                                    self.template.clone(),
                                ));
                            }
                            RenderError::InvalidArgumentInteger { .. }
                            | RenderError::InvalidArgumentString { .. } => {
                                return Err(PyValueError::with_source_code(
                                    err.into(),
                                    self.template.clone(),
                                ));
                            }
                            RenderError::OverflowError { .. }
                            | RenderError::InvalidArgumentFloat { .. } => {
                                return Err(PyOverflowError::with_source_code(
                                    err.into(),
                                    self.template.clone(),
                                ));
                            }
                            RenderError::TupleUnpackError { .. } => {
                                return Err(PyValueError::with_source_code(
                                    err.into(),
                                    self.template.clone(),
                                ));
                            }
                        }
                    }
                }
            }
            Ok(rendered)
        }
    }

    #[pymethods]
    impl Template {
        #[pyo3(signature = (context=None, request=None))]
        pub fn render(
            &self,
            py: Python<'_>,
            context: Option<Bound<'_, PyDict>>,
            request: Option<Bound<'_, PyAny>>,
        ) -> PyResult<String> {
            let mut base_context = HashMap::from([
                ("None".to_string(), py.None()),
                ("True".to_string(), PyBool::new(py, true).to_owned().into()),
                (
                    "False".to_string(),
                    PyBool::new(py, false).to_owned().into(),
                ),
            ]);
            if let Some(context) = context {
                let new_context: HashMap<_, _> = context.extract()?;
                base_context.extend(new_context);
            };
            let request = request.map(|request| request.unbind());
            let mut context = Context::new(base_context, request, self.autoescape);
            self._render(py, &mut context)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::django_rusty_templates::*;

    use pyo3::Python;
    use pyo3::types::{PyDict, PyDictMethods, PyList, PyString};

    #[test]
    fn test_syntax_error() {
        Python::initialize();

        Python::attach(|py| {
            let mut filename = std::env::current_dir().unwrap();
            filename.push("tests");
            filename.push("templates");
            filename.push("parse_error.txt");

            let expected = format!(
                "TemplateSyntaxError:   × Empty variable tag
   ╭─[{}:1:28]
 1 │ This is an empty variable: {{{{ }}}}
   ·                            ──┬──
   ·                              ╰── here
   ╰────
",
                filename.display(),
            );

            let engine = EngineData::empty();
            let template_string = std::fs::read_to_string(&filename).unwrap();
            let error = temp_env::with_var("NO_COLOR", Some("1"), || {
                Template::new(py, &template_string, filename, &engine).unwrap_err()
            });

            let error_string = format!("{error}");
            assert_eq!(error_string, expected);
        })
    }

    #[test]
    fn test_syntax_error_from_string() {
        Python::initialize();

        Python::attach(|py| {
            let engine = EngineData::empty();
            let template_string = "{{ foo.bar|title'foo' }}".to_string();
            let error = temp_env::with_var("NO_COLOR", Some("1"), || {
                Template::new_from_string(py, template_string, &engine).unwrap_err()
            });

            let expected = "TemplateSyntaxError:   × Could not parse the remainder
   ╭────
 1 │ {{ foo.bar|title'foo' }}
   ·                 ──┬──
   ·                   ╰── here
   ╰────
";

            let error_string = format!("{error}");
            assert_eq!(error_string, expected);
        })
    }

    #[test]
    fn test_render_empty_template() {
        Python::initialize();

        Python::attach(|py| {
            let engine = EngineData::empty();
            let template_string = "".to_string();
            let template = Template::new_from_string(py, template_string, &engine).unwrap();
            let context = PyDict::new(py);

            assert_eq!(template.render(py, Some(context), None).unwrap(), "");
        })
    }

    #[test]
    fn test_render_template_variable() {
        Python::initialize();

        Python::attach(|py| {
            let engine = EngineData::empty();
            let template_string = "Hello {{ user }}!".to_string();
            let template = Template::new_from_string(py, template_string, &engine).unwrap();
            let context = PyDict::new(py);
            context.set_item("user", "Lily").unwrap();

            assert_eq!(
                template.render(py, Some(context), None).unwrap(),
                "Hello Lily!"
            );
        })
    }

    #[test]
    fn test_render_template_unknown_variable() {
        Python::initialize();

        Python::attach(|py| {
            let engine = EngineData::empty();
            let template_string = "Hello {{ user }}!".to_string();
            let template = Template::new_from_string(py, template_string, &engine).unwrap();
            let context = PyDict::new(py);

            assert_eq!(template.render(py, Some(context), None).unwrap(), "Hello !");
        })
    }

    #[test]
    fn test_render_template_variable_nested() {
        Python::initialize();

        Python::attach(|py| {
            let engine = EngineData::empty();
            let template_string = "Hello {{ user.profile.names.0 }}!".to_string();
            let template = Template::new_from_string(py, template_string, &engine).unwrap();
            let locals = PyDict::new(py);
            py.run(
                cr#"
class User:
    def __init__(self, names):
        self.profile = {"names": names}

user = User(["Lily"])
"#,
                None,
                Some(&locals),
            )
            .unwrap();
            let user = locals.get_item("user").unwrap().unwrap();
            let context = PyDict::new(py);
            context.set_item("user", user.into_any()).unwrap();

            assert_eq!(
                template.render(py, Some(context), None).unwrap(),
                "Hello Lily!"
            );
        })
    }

    #[test]
    fn test_engine_from_string() {
        Python::initialize();

        Python::attach(|py| {
            let engine = Engine::new(
                py,
                None,
                false,
                None,
                false,
                None,
                "".to_string(),
                "utf-8".to_string(),
                None,
                None,
                false,
            )
            .unwrap();
            let template_string = PyString::new(py, "Hello {{ user }}!");
            let template = engine.from_string(template_string).unwrap();
            let context = PyDict::new(py);

            assert_eq!(template.render(py, Some(context), None).unwrap(), "Hello !");
        })
    }

    #[test]
    fn test_clone_template() {
        use std::collections::HashMap;

        use pyo3::IntoPyObject;
        use pyo3::types::{PyAnyMethods, PyListMethods};

        Python::initialize();

        Python::attach(|py| {
            let cwd = std::env::current_dir().unwrap();
            let sys_path = py.import("sys").unwrap().getattr("path").unwrap();
            let sys_path = sys_path.cast().unwrap();
            sys_path.append(cwd.to_string_lossy()).unwrap();
            let mut engine = Engine::new(
                py,
                Some(vec!["tests/templates"].into_pyobject(py).unwrap()),
                false,
                None,
                false,
                None,
                "".to_string(),
                "utf-8".to_string(),
                Some(
                    HashMap::from([("custom_filters", "tests.templatetags.custom_filters")])
                        .into_pyobject(py)
                        .unwrap()
                        .into_any(),
                ),
                None,
                false,
            )
            .unwrap();
            let template = engine
                .get_template(py, "full_example.html".to_string())
                .unwrap();
            let cloned = template.clone();
            assert_eq!(cloned, template);
        })
    }

    #[test]
    fn test_engine_attributes() {
        use std::collections::HashMap;

        use pyo3::IntoPyObject;
        use pyo3::types::{PyAnyMethods, PyListMethods};

        Python::initialize();

        Python::attach(|py| {
            let cwd = std::env::current_dir().unwrap();
            let sys_path = py.import("sys").unwrap().getattr("path").unwrap();
            let sys_path = sys_path.cast().unwrap();
            sys_path.append(cwd.to_string_lossy()).unwrap();

            let engine = Engine::new(
                py,
                Some(
                    vec!["tests/templates", "other/templates"]
                        .into_pyobject(py)
                        .unwrap(),
                ),
                true,
                Some(
                    vec!["django.template.context_processors.debug"]
                        .into_pyobject(py)
                        .unwrap(),
                ),
                true,
                None,
                "INVALID".to_string(),
                "utf-8".to_string(),
                Some(
                    HashMap::from([("custom_filters", "tests.templatetags.custom_filters")])
                        .into_pyobject(py)
                        .unwrap()
                        .into_any(),
                ),
                None,
                false,
            )
            .unwrap();

            let py_engine = engine.into_pyobject(py).unwrap();
            py_engine.getattr("dirs").unwrap();
            py_engine.getattr("app_dirs").unwrap();
            py_engine.getattr("context_processors").unwrap();
            py_engine.getattr("debug").unwrap();
            py_engine.getattr("string_if_invalid").unwrap();
            py_engine.getattr("file_charset").unwrap();
            py_engine.getattr("builtins").unwrap();
            py_engine.getattr("libraries").unwrap();
            py_engine.getattr("autoescape").unwrap();

            // Non-trivial getters
            let dirs: Vec<String> = py_engine.getattr("dirs").unwrap().extract().unwrap();
            assert_eq!(dirs.len(), 2);
            assert!(dirs[0].ends_with("tests/templates"));
            assert!(dirs[1].ends_with("other/templates"));

            let file_charset: String = py_engine
                .getattr("file_charset")
                .unwrap()
                .extract()
                .unwrap();
            assert_eq!(file_charset, "UTF-8");

            // TODO: support this once #89 lands
            // let loaders: Vec<String> = py_engine.getattr("loaders").unwrap().extract().unwrap();
            // assert_eq!(loaders.len(), 1);
            // assert_eq!(loaders[0], "django.template.loaders.cached.Loader");
        })
    }

    #[test]
    fn test_engine_app_dirs_with_loaders() {
        Python::initialize();

        Python::attach(|py| {
            let loaders = PyList::empty(py).into_any();
            let app_dirs = true;
            let engine_error = Engine::new(
                py,
                None,
                app_dirs,
                None,
                false,
                Some(loaders),
                "".to_string(),
                "utf-8".to_string(),
                None,
                None,
                false,
            )
            .unwrap_err();

            assert!(engine_error.is_instance_of::<ImproperlyConfigured>(py));
            let message = "app_dirs must not be set when loaders is defined.";
            assert_eq!(engine_error.value(py).to_string(), message);
        })
    }
}
