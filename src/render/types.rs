use std::borrow::Cow;
use std::collections::BTreeMap;
use std::collections::HashMap;
use std::collections::HashSet;
use std::iter::zip;
use std::sync::{Arc, Mutex};

use html_escape::encode_quoted_attribute;
use miette::SourceSpan;
use num_bigint::{BigInt, ToBigInt};
use num_traits::{ToPrimitive, Zero};
use pyo3::exceptions::{PyAttributeError, PyKeyError, PyTypeError};
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::sync::{MutexExt, PyOnceLock};
use pyo3::types::{PyBool, PyDict, PyInt, PyString, PyType};

use crate::error::{AnnotatePyErr, PyRenderError, RenderError};
use crate::utils::PyResultMethods;
use dtl_lexer::types::{At, TemplateString};

static MARK_SAFE: PyOnceLock<Py<PyAny>> = PyOnceLock::new();

#[derive(Debug, Clone)]
pub struct CycleState {
    pub values: Vec<String>,
    pub index: usize,
}


#[derive(Debug, Clone)]
pub struct ForLoop {
    count: usize,
    len: usize,
}

impl ForLoop {
    pub fn counter0(&self) -> usize {
        self.count
    }

    pub fn counter(&self) -> usize {
        self.count + 1
    }

    pub fn rev_counter(&self) -> usize {
        self.len - self.count
    }

    pub fn rev_counter0(&self) -> usize {
        self.len - self.count - 1
    }

    pub fn first(&self) -> bool {
        self.count == 0
    }

    pub fn last(&self) -> bool {
        self.count + 1 == self.len
    }
}

#[derive(Debug, Default)]
pub struct Context {
    context: HashMap<String, Vec<Py<PyAny>>>,
    loops: Vec<ForLoop>,
    pub request: Option<Py<PyAny>>,
    pub autoescape: bool,
    names: Vec<HashSet<String>>,
    pub cycles: HashMap<String, CycleState>,
}

impl Context {
    pub fn new(
        context: HashMap<String, Py<PyAny>>,
        request: Option<Py<PyAny>>,
        autoescape: bool,
    ) -> Self {
        let context = context.into_iter().map(|(k, v)| (k, vec![v])).collect();
        Self {
            request,
            context,
            autoescape,
            loops: Vec::new(),
            names: Vec::new(),
            cycles: HashMap::new(),
        }
    }

    pub fn clone_ref(&self, py: Python<'_>) -> Self {
        Self {
            request: self.request.as_ref().map(|v| v.clone_ref(py)),
            context: self
                .context
                .iter()
                .map(|(k, v)| (k.clone(), v.iter().map(|v| v.clone_ref(py)).collect()))
                .collect(),
            autoescape: self.autoescape,
            loops: self.loops.clone(),
            names: self.names.clone(),
            cycles: self.cycles.clone(),
        }
    }

    pub fn get(&self, key: &str) -> Option<&Py<PyAny>> {
        self.context.get(key)?.last()
    }

    pub fn display(&self, py: Python<'_>) -> String {
        let context: BTreeMap<_, _> = self
            .context
            .iter()
            .filter_map(|(k, v)| Some((k, v.last()?.bind(py))))
            .collect();
        format!("{context:?}")
    }

    fn _insert(&mut self, key: String, value: Bound<'_, PyAny>, replace: bool) {
        let value = value.unbind();
        match self.context.entry(key) {
            std::collections::hash_map::Entry::Occupied(mut entry) => {
                let values = entry.get_mut();
                if replace {
                    values.pop();
                }
                values.push(value);
            }
            std::collections::hash_map::Entry::Vacant(entry) => {
                entry.insert(vec![value]);
            }
        }
    }

    pub fn insert(&mut self, key: String, value: Bound<'_, PyAny>) {
        self._insert(key, value, true);
    }

    pub fn push_variable(&mut self, name: String, value: Bound<'_, PyAny>, index: usize) {
        let replace = index != 0;
        if !replace {
            let mut names_set = HashSet::new();
            names_set.insert(name.clone());
            self.names.push(names_set);
        }
        self._insert(name, value, replace);
    }

    pub fn push_variables(
        &mut self,
        names: &Vec<String>,
        names_at: At,
        values: Bound<'_, PyAny>,
        values_at: At,
        index: usize,
        template: TemplateString<'_>,
    ) -> Result<(), PyRenderError> {
        let replace = index != 0;
        if !replace {
            let names_set = names.iter().cloned().collect();
            self.names.push(names_set);
        }
        if names.len() == 1 {
            self._insert(names[0].clone(), values, replace);
        } else {
            let py = values.py();
            let values: Vec<_> = match values.try_iter() {
                Ok(values) => match values.collect() {
                    Ok(values) => values,
                    Err(error) => {
                        let error = error.annotate(py, values_at, "while unpacking this", template);
                        return Err(error.into());
                    }
                },
                Err(error) if error.is_instance_of::<PyTypeError>(py) => {
                    return Err(RenderError::TupleUnpackError {
                        expected_count: names.len(),
                        actual_count: 1,
                        expected_at: names_at.into(),
                        actual_at: values_at.into(),
                    }
                    .into());
                }
                Err(error) => {
                    let error = error.annotate(py, values_at, "while iterating this", template);
                    return Err(error.into());
                }
            };
            if names.len() == values.len() {
                for (name, value) in zip(names, values) {
                    self._insert(name.clone(), value, replace);
                }
            } else {
                return Err(RenderError::TupleUnpackError {
                    expected_count: names.len(),
                    actual_count: values.len(),
                    expected_at: names_at.into(),
                    actual_at: values_at.into(),
                }
                .into());
            }
        }
        Ok(())
    }

    fn _pop_variable(&mut self, name: &str) {
        let values = self
            .context
            .get_mut(name)
            .expect("Variable should have been pushed before");
        values.pop();
    }

    pub fn pop_variables(&mut self) {
        if let Some(names) = self.names.pop() {
            for name in names {
                self._pop_variable(&name);
            }
        }
    }

    pub fn push_for_loop(&mut self, len: usize) {
        self.loops.push(ForLoop { count: 0, len });
    }

    pub fn increment_for_loop(&mut self) {
        let for_loop = self
            .loops
            .last_mut()
            .expect("Called within an active for loop");
        for_loop.count += 1;
    }

    pub fn pop_for_loop(&mut self) {
        self.loops
            .pop()
            .expect("Called when exiting an active for loop");
    }

    pub fn get_for_loop(&self, depth: usize) -> Option<&ForLoop> {
        let index = self.loops.len().checked_sub(depth + 1)?;
        self.loops.get(index)
    }

    pub fn render_for_loop(&self, py: Python<'_>, depth: usize) -> String {
        let mut forloop_dict = PyDict::new(py);
        for forloop in self.loops.iter().rev().take(self.loops.len() - depth) {
            let dict = PyDict::new(py);
            dict.set_item("parentloop", forloop_dict)
                .expect("Can always set a str: dict key/value");
            dict.set_item("counter0", forloop.counter0())
                .expect("Can always set a str: int key/value");
            dict.set_item("counter", forloop.counter())
                .expect("Can always set a str: int key/value");
            dict.set_item("revcounter", forloop.rev_counter())
                .expect("Can always set a str: int key/value");
            dict.set_item("revcounter0", forloop.rev_counter0())
                .expect("Can always set a str: int key/value");
            dict.set_item("first", forloop.first())
                .expect("Can always set a str: bool key/value");
            dict.set_item("last", forloop.last())
                .expect("Can always set a str: bool key/value");
            forloop_dict = dict;
        }

        let forloop_str = forloop_dict
            .str()
            .expect("All elements of the dictionary can be converted to a string");
        forloop_str.to_string()
    }
}

#[pyclass(mapping)]
#[derive(Clone)]
pub struct PyContext {
    pub context: Arc<Mutex<Context>>,
}

impl PyContext {
    pub fn new(context: Context) -> Self {
        Self {
            context: Arc::new(Mutex::new(context)),
        }
    }
}

#[pymethods]
impl PyContext {
    #[getter]
    fn request<'py>(&self, py: Python<'py>) -> Option<Bound<'py, PyAny>> {
        let guard = self
            .context
            .lock_py_attached(py)
            .expect("Mutex should not be poisoned");
        guard
            .request
            .as_ref()
            .map(|request| request.bind(py).clone())
    }

    fn get<'py>(
        &self,
        py: Python<'py>,
        key: String,
        fallback: Bound<'py, PyAny>,
    ) -> Bound<'py, PyAny> {
        let guard = self
            .context
            .lock_py_attached(py)
            .expect("Mutex should not be poisoned");
        match guard.get(&key) {
            Some(value) => value.bind(py).clone(),
            None => fallback,
        }
    }

    fn __contains__(&self, py: Python<'_>, key: String) -> bool {
        let guard = self
            .context
            .lock_py_attached(py)
            .expect("Mutex should not be poisoned");
        guard.get(&key).is_some()
    }

    fn __getitem__<'py>(&self, py: Python<'py>, key: String) -> PyResult<Bound<'py, PyAny>> {
        let guard = self
            .context
            .lock_py_attached(py)
            .expect("Mutex should not be poisoned");
        match guard.get(&key) {
            Some(value) => Ok(value.bind(py).clone()),
            None => Err(PyKeyError::new_err(key)),
        }
    }

    fn __setitem__<'py>(&self, py: Python<'py>, key: String, value: Bound<'py, PyAny>) {
        let mut guard = self
            .context
            .lock_py_attached(py)
            .expect("Mutex should not be poisoned");
        if let Some(last) = guard.names.last_mut() {
            last.insert(key.clone());
        }
        guard.insert(key, value);
    }
}

#[derive(Debug, IntoPyObject)]
pub enum ContentString<'t> {
    String(Cow<'t, str>),
    HtmlSafe(Cow<'t, str>),
    HtmlUnsafe(Cow<'t, str>),
}

#[allow(clippy::needless_lifetimes)] // https://github.com/rust-lang/rust-clippy/issues/13923
impl<'t, 'py> ContentString<'t> {
    pub fn content(self) -> Cow<'t, str> {
        match self {
            Self::String(content) | Self::HtmlSafe(content) => content,
            Self::HtmlUnsafe(content) => Cow::Owned(encode_quoted_attribute(&content).to_string()),
        }
    }

    pub fn as_raw(&self) -> &Cow<'t, str> {
        match self {
            Self::String(content) | Self::HtmlSafe(content) | Self::HtmlUnsafe(content) => content,
        }
    }

    pub fn into_raw(self) -> Cow<'t, str> {
        match self {
            Self::String(content) | Self::HtmlSafe(content) | Self::HtmlUnsafe(content) => content,
        }
    }

    pub fn map_content(self, f: impl FnOnce(Cow<'t, str>) -> Cow<'t, str>) -> Content<'t, 'py> {
        Content::String(match self {
            Self::String(content) => Self::String(f(content)),
            Self::HtmlSafe(content) => Self::HtmlSafe(f(content)),
            Self::HtmlUnsafe(content) => Self::HtmlUnsafe(f(content)),
        })
    }
}

fn resolve_python<'t>(value: Bound<'_, PyAny>, context: &Context) -> PyResult<ContentString<'t>> {
    if !context.autoescape {
        return Ok(ContentString::String(
            value.str()?.extract::<String>()?.into(),
        ));
    }
    let py = value.py();

    let value = match value.is_instance_of::<PyString>() {
        true => value,
        false => value.str()?.into_any(),
    };
    Ok(
        match value
            .getattr(intern!(py, "__html__"))
            .ok_or_isinstance_of::<PyAttributeError>(py)?
        {
            Ok(html) => ContentString::HtmlSafe(html.call0()?.extract::<String>()?.into()),
            Err(_) => ContentString::HtmlUnsafe(value.str()?.extract::<String>()?.into()),
        },
    )
}

fn resolve_bigint(bigint: BigInt, at: At) -> Result<usize, PyRenderError> {
    match bigint.to_isize() {
        Some(n) => {
            let n = n.max(0);
            #[allow(clippy::cast_sign_loss)]
            let n = n as usize;
            Ok(n)
        }
        None => Err(RenderError::OverflowError {
            argument: bigint.to_string(),
            argument_at: at.into(),
        }
        .into()),
    }
}

#[derive(Debug, IntoPyObject)]
pub enum Content<'t, 'py> {
    Py(Bound<'py, PyAny>),
    String(ContentString<'t>),
    Float(f64),
    Int(BigInt),
    Bool(bool),
}

impl<'t, 'py> Content<'t, 'py> {
    pub fn render(self, context: &Context) -> PyResult<Cow<'t, str>> {
        Ok(match self {
            Self::Py(content) => resolve_python(content, context)?.content(),
            Self::String(content) => content.content(),
            Self::Float(content) => content.to_string().into(),
            Self::Int(content) => content.to_string().into(),
            Self::Bool(true) => "True".into(),
            Self::Bool(false) => "False".into(),
        })
    }

    pub fn resolve_string(self, context: &Context) -> PyResult<ContentString<'t>> {
        Ok(match self {
            Self::String(content) => content,
            Self::Float(content) => ContentString::String(content.to_string().into()),
            Self::Int(content) => ContentString::String(content.to_string().into()),
            Self::Py(content) => return resolve_python(content, context),
            Self::Bool(true) => ContentString::String(Cow::Borrowed("True")),
            Self::Bool(false) => ContentString::String(Cow::Borrowed("False")),
        })
    }
    /// Resolve to a string, raising an error if the content is not a string or a string-like Python object
    pub fn resolve_string_strict(
        self,
        context: &Context,
        argument_at: SourceSpan,
    ) -> Result<ContentString<'t>, PyRenderError> {
        match self {
            Self::String(content) => Ok(content),
            Self::Py(content) if content.is_instance_of::<PyString>() => {
                Ok(resolve_python(content, context)?)
            }
            _ => Err(RenderError::InvalidArgumentString { argument_at }.into()),
        }
    }

    pub fn to_bigint(&self) -> Option<BigInt> {
        match self {
            Self::Int(left) => Some(left.clone()),
            Self::String(left) => left.as_raw().parse::<BigInt>().ok(),
            Self::Float(left) => left.trunc().to_bigint(),
            Self::Py(left) => match left.extract::<BigInt>() {
                Ok(left) => Some(left),
                Err(_) => {
                    let int = PyType::new::<PyInt>(left.py());
                    let left = int.call1((left,)).ok()?;
                    Some(
                        left.extract::<BigInt>()
                            .expect("Python integers are BigInt compatible"),
                    )
                }
            },
            Self::Bool(true) => 1.to_bigint(),
            Self::Bool(false) => 0.to_bigint(),
        }
    }

    /// Convert Content to usize, providing detailed errors if the conversion fails
    pub fn resolve_usize(self, argument_at: At) -> Result<usize, PyRenderError> {
        match self {
            Self::Int(n) => resolve_bigint(n, argument_at),
            Self::String(s) => match s.as_raw().parse::<BigInt>() {
                Ok(n) => resolve_bigint(n, argument_at),
                Err(_) => Err(RenderError::InvalidArgumentInteger {
                    argument: format!("'{}'", s.as_raw()),
                    argument_at: argument_at.into(),
                }
                .into()),
            },
            Self::Float(f) => match f.trunc().to_bigint() {
                Some(n) => resolve_bigint(n, argument_at),
                None => Err(RenderError::InvalidArgumentFloat {
                    argument: f.to_string(),
                    argument_at: argument_at.into(),
                }
                .into()),
            },
            Self::Py(obj) => match obj.extract::<BigInt>() {
                Ok(n) => resolve_bigint(n, argument_at),
                Err(_) => {
                    let argument = obj.to_string();
                    let argument_at = argument_at.into();
                    match obj.extract::<f64>() {
                        Ok(_) => Err(RenderError::InvalidArgumentFloat {
                            argument,
                            argument_at,
                        }
                        .into()),
                        Err(_) => Err(RenderError::InvalidArgumentInteger {
                            argument,
                            argument_at,
                        }
                        .into()),
                    }
                }
            },
            Self::Bool(true) => Ok(1),
            Self::Bool(false) => Ok(0),
        }
    }
    pub fn to_bool(&self) -> PyResult<bool> {
        Ok(match self {
            Self::Bool(b) => *b,
            Self::Int(n) => !n.is_zero(),
            Self::Float(f) => !f.is_zero(),
            Self::String(s) => !s.as_raw().is_empty(),
            Self::Py(obj) => obj.is_truthy()?,
        })
    }

    pub fn to_py(&self, py: Python<'py>) -> Bound<'py, PyAny> {
        match self {
            Self::Py(object) => object.clone(),
            Self::Int(i) => i
                .into_pyobject(py)
                .expect("A BigInt can always be converted to a Python int.")
                .into_any(),
            Self::Float(f) => f
                .into_pyobject(py)
                .expect("An f64 can always be converted to a Python float.")
                .into_any(),
            Self::String(s) => match s {
                ContentString::String(s) | ContentString::HtmlUnsafe(s) => s
                    .into_pyobject(py)
                    .expect("A string can always be converted to a Python str.")
                    .into_any(),
                ContentString::HtmlSafe(s) => {
                    let string = s
                        .into_pyobject(py)
                        .expect("A string can always be converted to a Python str.");
                    let mark_safe = MARK_SAFE
                        .import(py, "django.utils.safestring", "mark_safe")
                        .expect("Should be able to import `django.utils.safestring.mark_safe`");
                    mark_safe
                        .call1((string,))
                        .expect("`mark_safe` should not raise if given a string")
                }
            },
            Self::Bool(b) => PyBool::new(py, *b).to_owned().into_any(),
        }
    }
}
pub trait IntoOwnedContent<'t, 'py> {
    fn into_content(self) -> Content<'t, 'py>;
}

pub trait AsBorrowedContent<'a, 't, 'py>
where
    'a: 't,
{
    fn as_content(&'a self) -> Content<'t, 'py>;
}

impl<'a, 't, 'py> AsBorrowedContent<'a, 't, 'py> for str
where
    'a: 't,
{
    fn as_content(&'a self) -> Content<'t, 'py> {
        Content::String(ContentString::String(Cow::Borrowed(self)))
    }
}

impl<'t, 'py> IntoOwnedContent<'t, 'py> for String {
    fn into_content(self) -> Content<'t, 'py> {
        Content::String(ContentString::String(Cow::Owned(self)))
    }
}

impl<'t, 'py> IntoOwnedContent<'t, 'py> for Cow<'t, str> {
    fn into_content(self) -> Content<'t, 'py> {
        Content::String(ContentString::String(self))
    }
}
