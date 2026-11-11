use std::borrow::Cow;
use std::path::{Path, PathBuf};

use miette::{Diagnostic, NamedSource, SourceSpan};
use sugar_path::SugarPath;
use thiserror::Error;

use dtl_lexer::types::At;

#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
#[error(
    "The relative path '{template_path}' points outside the file hierarchy that template '{origin}' is in."
)]
pub struct Outside {
    #[label("relative path")]
    pub at: SourceSpan,
    pub origin: PathBuf,
    pub template_path: String,
    #[source_code]
    pub src: NamedSource<String>,
}

#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
#[error("The relative path '{path}' cannot be evaluated due to an unknown template origin.")]
pub struct UnknownOrigin {
    path: String,
    #[label("here")]
    at: SourceSpan,
    #[source_code]
    src: String,
}

#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
pub enum RelativePathError {
    #[error(transparent)]
    #[diagnostic(transparent)]
    Outside(Box<Outside>),
    #[error(transparent)]
    #[diagnostic(transparent)]
    UnknownOrigin(Box<UnknownOrigin>),
}

pub fn construct_relative_path<'a>(
    path: &'a str,
    origin: Option<&'a str>,
    at: At,
    src: &str,
) -> Result<Option<Cow<'a, str>>, RelativePathError> {
    let adjacent = path.starts_with("./");
    if !adjacent && !path.starts_with("../") {
        return Ok(None);
    }
    match origin {
        Some(origin_str) => {
            let origin = Path::new(origin_str);
            let path = match origin.parent() {
                None if adjacent => Path::new(path).normalize().into_owned(),
                None => {
                    return Err(RelativePathError::Outside(Box::new(Outside {
                        at: at.into(),
                        origin: origin.to_path_buf(),
                        template_path: path.to_string(),
                        src: NamedSource::new(origin_str, src.to_string()),
                    })));
                }
                Some(directory) => {
                    let new_path = Path::join(directory, path).normalize().into_owned();
                    if new_path.starts_with("../") {
                        return Err(RelativePathError::Outside(Box::new(Outside {
                            at: at.into(),
                            origin: origin.to_path_buf(),
                            template_path: path.to_string(),
                            src: NamedSource::new(origin_str, src.to_string()),
                        })));
                    }
                    new_path
                }
            };
            Ok(Some(Cow::Owned(
                path.to_str()
                    .expect("Template names should be valid unicode.")
                    .to_string(),
            )))
        }
        None => Err(RelativePathError::UnknownOrigin(Box::new(UnknownOrigin {
            at: at.into(),
            path: path.to_string(),
            src: src.to_string(),
        }))),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_construct_adjacent_path_origin_root() {
        let path = "./foo.txt";
        let origin = Some("/");
        let at = (0, 8);
        let src = "abcdefgh";
        assert_eq!(
            construct_relative_path(path, origin, at, src)
                .unwrap()
                .unwrap(),
            "foo.txt"
        );
    }

    #[test]
    fn test_construct_parent_path_origin_root() {
        let path = "../foo.txt";
        let origin = "/";
        let at = (0, 8);
        let src = "abcdefgh";
        assert_eq!(
            construct_relative_path(path, Some(origin), at, src).unwrap_err(),
            RelativePathError::Outside(Box::new(Outside {
                at: at.into(),
                origin: origin.into(),
                template_path: path.to_string(),
                src: NamedSource::new(origin, src.to_string()),
            }))
        );
    }

    #[test]
    fn test_construct_adjacent_path_origin_empty_string() {
        let path = "./foo.txt";
        let origin = Some("");
        let at = (0, 8);
        let src = "abcdefgh";
        assert_eq!(
            construct_relative_path(path, origin, at, src)
                .unwrap()
                .unwrap(),
            "foo.txt"
        );
    }

    #[test]
    fn test_construct_parent_path_origin_empty_string() {
        let path = "../foo.txt";
        let origin = "";
        let at = (0, 8);
        let src = "abcdefgh";
        assert_eq!(
            construct_relative_path(path, Some(origin), at, src).unwrap_err(),
            RelativePathError::Outside(Box::new(Outside {
                at: at.into(),
                origin: origin.into(),
                template_path: path.to_string(),
                src: NamedSource::new(origin, src.to_string()),
            }))
        );
    }
}
