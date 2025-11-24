use pyo3::prelude::*;
use pyo3::type_object::PyTypeInfo;

pub trait PyResultMethods<T> {
    fn ok_or_isinstance_of<E>(self, py: Python<'_>) -> PyResult<PyResult<T>>
    where
        E: PyTypeInfo;
}

impl<T> PyResultMethods<T> for PyResult<T> {
    fn ok_or_isinstance_of<E>(self, py: Python<'_>) -> PyResult<Self>
    where
        E: PyTypeInfo,
    {
        match self {
            Ok(obj) => Ok(Ok(obj)),
            Err(e) if e.is_instance_of::<E>(py) => Ok(Err(e)),
            Err(e) => Err(e),
        }
    }
}
