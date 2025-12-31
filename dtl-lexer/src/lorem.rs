use rand::Rng;
use rand::seq::SliceRandom;

static COMMON_P: &str = "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod \
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud \
exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in \
reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint \
occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.";

static WORDS: [&str; 182] = [
    "exercitationem",
    "perferendis",
    "perspiciatis",
    "laborum",
    "eveniet",
    "sunt",
    "iure",
    "name",
    "nobis",
    "eum",
    "cum",
    "officiis",
    "excepturi",
    "odio",
    "consectetur",
    "quasi",
    "aut",
    "quisquam",
    "vel",
    "eligendi",
    "itaque",
    "non",
    "odit",
    "tempore",
    "quaerat",
    "dignissimos",
    "facilis",
    "neque",
    "nihil",
    "expedita",
    "vitae",
    "vero",
    "ipsum",
    "nisi",
    "animi",
    "cumque",
    "pariatur",
    "velit",
    "modi",
    "natus",
    "iusto",
    "eaque",
    "sequi",
    "illo",
    "sed",
    "ex",
    "et",
    "voluptatibus",
    "tempora",
    "veritatis",
    "ratione",
    "assumenda",
    "incidunt",
    "nostrum",
    "placeat",
    "aliquid",
    "fuga",
    "provident",
    "praesentium",
    "rem",
    "necessitatibus",
    "suscipit",
    "adipisci",
    "quidem",
    "possimus",
    "voluptas",
    "debitis",
    "sint",
    "accusantium",
    "unde",
    "sapiente",
    "voluptate",
    "qui",
    "aspernatur",
    "laudantium",
    "soluta",
    "amet",
    "quo",
    "aliquam",
    "saepe",
    "culpa",
    "libero",
    "ipsa",
    "dicta",
    "reiciendis",
    "nesciunt",
    "doloribus",
    "autem",
    "impedit",
    "minima",
    "maiores",
    "repudiandae",
    "ipsam",
    "obcaecati",
    "ullam",
    "enim",
    "totam",
    "delectus",
    "ducimus",
    "quis",
    "voluptates",
    "dolores",
    "molestiae",
    "harum",
    "dolorem",
    "quia",
    "voluptatem",
    "molestias",
    "magni",
    "distinctio",
    "omnis",
    "illum",
    "dolorum",
    "voluptatum",
    "ea",
    "quas",
    "quam",
    "corporis",
    "quae",
    "blanditiis",
    "atque",
    "deserunt",
    "laboriosam",
    "earum",
    "consequuntur",
    "hic",
    "cupiditate",
    "quibusdam",
    "accusamus",
    "ut",
    "rerum",
    "error",
    "minus",
    "eius",
    "ab",
    "ad",
    "nemo",
    "fugit",
    "officia",
    "at",
    "in",
    "id",
    "quos",
    "reprehenderit",
    "numquam",
    "iste",
    "fugiat",
    "sit",
    "inventore",
    "beatae",
    "repellendus",
    "magnam",
    "recusandae",
    "quod",
    "explicabo",
    "doloremque",
    "aperiam",
    "consequatur",
    "asperiores",
    "commodi",
    "option",
    "dolor",
    "labore",
    "temporibus",
    "repellat",
    "veniam",
    "architecto",
    "est",
    "esse",
    "mollitia",
    "nulla",
    "a",
    "similique",
    "eos",
    "alias",
    "dolore",
    "tenetur",
    "deleniti",
    "porro",
    "facere",
    "maxime",
    "corrupti",
];

static COMMON_WORDS: [&str; 19] = [
    "lorem",
    "ipsum",
    "dolor",
    "sit",
    "amet",
    "consectetur",
    "adipisicing",
    "elit",
    "sed",
    "do",
    "eiusmod",
    "tempor",
    "incididunt",
    "ut",
    "labore",
    "et",
    "dolore",
    "magna",
    "aliqua",
];

pub fn sentence() -> String {
    use rand::Rng;
    use rand::seq::SliceRandom;

    let mut rng = rand::thread_rng();
    let num_sections = rng.gen_range(1..=5);
    let mut sections = Vec::with_capacity(num_sections);

    for _ in 0..num_sections {
        let num_words = rng.gen_range(3..=12);
        let selected_words: Vec<&str> = WORDS
            .choose_multiple(&mut rng, num_words)
            .copied()
            .collect();

        sections.push(selected_words.join(" "));
    }

    let mut sentence = sections.join(", ");

    if let Some(first) = sentence.chars().next() {
        let upper = first.to_uppercase().to_string();
        let rest = &sentence[first.len_utf8()..];
        sentence = format!("{upper}{rest}");
    }

    let punctuation = if rng.gen_bool(0.5) { "?" } else { "." };
    sentence.push_str(punctuation);

    sentence
}

pub fn paragraph() -> String {
    let num_sentences = rand::thread_rng().gen_range(1..=4);
    (0..num_sentences)
        .map(|_| sentence())
        .collect::<Vec<String>>()
        .join(" ")
}

pub fn paragraphs(count: usize, common: bool) -> Vec<String> {
    let mut paras = Vec::with_capacity(count);

    for i in 0..count {
        if common && i == 0 {
            paras.push(COMMON_P.to_string());
        } else {
            paras.push(paragraph());
        }
    }

    paras
}

pub fn words(count: usize, common: bool) -> String {
    if common && count <= COMMON_WORDS.len() {
        return COMMON_WORDS[..count].join(" ");
    }
    let mut rng = rand::thread_rng();
    let mut word_list: Vec<&str> = Vec::with_capacity(count);
    if common {
        word_list.extend(&COMMON_WORDS);
    }
    let mut remaining = count - word_list.len();
    while remaining > 0 {
        let take = remaining.min(WORDS.len());
        let sampled = WORDS.choose_multiple(&mut rng, take);
        word_list.extend(sampled.cloned());
        remaining -= take;
    }
    word_list.join(" ")
}
