use num_bigint::BigInt;

use dtl_lexer::types::At;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Text {
    pub at: At,
}

impl Text {
    pub fn new(at: At) -> Self {
        Self { at }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct TranslatedText {
    pub at: At,
}

impl TranslatedText {
    pub fn new(at: At) -> Self {
        Self { at }
    }
}

#[derive(Clone, Debug, PartialEq)]
pub enum Variable {
    #[expect(clippy::enum_variant_names)]
    Variable(At),
    ForVariable(ForVariable),
    BlockSuper(At),
}

#[derive(Clone, Debug, PartialEq)]
pub enum ArgumentType {
    Variable(Variable),
    Text(Text),
    TranslatedText(TranslatedText),
    Int(BigInt),
    Float(f64),
}

#[derive(Clone, Debug, PartialEq)]
pub struct Argument {
    pub at: At,
    pub argument_type: ArgumentType,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ForVariableName {
    Counter,
    Counter0,
    RevCounter,
    RevCounter0,
    First,
    Last,
    Object,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ForVariable {
    pub variant: ForVariableName,
    pub parent_count: usize,
    pub at: At,
}
