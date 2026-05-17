SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "ja": "Japanese",
}


def get_language_name(code):

    return SUPPORTED_LANGUAGES.get(
        code,
        "English"
    )


def format_languages():

    return [
        {
            "code": k,
            "name": v
        }
        for k, v in SUPPORTED_LANGUAGES.items()
    ]