import re
from deep_translator import GoogleTranslator
from langchain.prompts.prompt import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains.llm import LLMChain

translation_prompt = """You are an intelligent assistant that translates text to the language: {language}. 
The text for translation is: ```{text}```

# Instructions
- Do not include any explanations or apologies in your responses.
- Provide only the translation of the text, nothing else.
- [IMPORTANT] Keep the format as it. 
- [IMPORTANT] DO NOT TRANSLATE any links, i.e. https://augmentor.upatras.gr/mod/quiz/view.php?id=15
- [IMPORTANT] DO NOT TRANSLATE any link titles, i.e. [ΑΣΚΗΣΗ1: Το δικό σου Matrix].
- [IMPORTANT] Translate the provided text in {language}.
- [IMPORTANT]Always translate in {language} all text, including expressions such as "Cognitive", "Average grade", "Analysis", "Recommendation", "Not studied resources", "Notes", etc.
- Reply with the translated text in the form```<translated text>```
"""
PROMPT = PromptTemplate(
    input_variables=["language", "text"], template=translation_prompt
)

translation_model = ChatOpenAI(model_name="...", 
                               temperature=0, 
                               openai_api_key="...")
translation_model = LLMChain(llm=translation_model, prompt=PROMPT)



abbr_languages = {'english':'en', 'greek': 'el', 'serbian': 'sr', 'lithuanian': 'lt'}
def translate(text:str=None, language:str=None, method:str="GoogleTranlator"):
    """
    Translates a given text to a specified language using the chosen translation method.

    Args:
        text (str): The text to be translated.
        language (str): The target language for translation.
        method (str, optional): The translation method to use. Valid options are "LLM" and "GoogleTranlator". 
                                Defaults to "GoogleTranlator".

    Returns:
        str: The translated text or the original text if translation fails.

    Raises:
        Prints a warning if an unknown method is provided or if translation errors occur.

    Method Details:
        - "LLM": Uses a custom translation model to perform translation.
        - "GoogleTranlator": Uses the GoogleTranslator API to translate the text. If the text is too long,
          it splits it into parts and translates each part separately.

    Translation Customizations:
        - Replaces certain terms in the translated text:
          - "student" → "learner"
          - "lesson" → "module"
          - "score" → "grade" (for English)
        - Ensures "augMENTOR" is retained in translated versions for Greek, Serbian, and Lithuanian.

    Warnings:
        - If "grade" is detected in non-English text, a warning is displayed indicating potential translation errors.
        - Google translation errors fall back to using the "LLM" method.
    """
    # Sanity check
    if method not in ["LLM", "GoogleTranlator"]:
        print("[ERROR] Not known translation methods. Valid  methods: 'LLM', 'GoogleTranlator'")
        return text
    
    if method == "LLM":
        return translation_model.run({"text": text, "language": language}).replace("```", "")

    source = "auto" if language == "english" else "english"

    try:
        if len(text) < 3000:
            translated_text = GoogleTranslator(source=source, target=abbr_languages[language]).translate(text)
        else:
            # Split text in parts
            text_parts = [""]
            for part in text.split("\n"):
                if len(part) > 3000: 
                    print("[WARNING] Text cannot be translated")
                    return text

                if len(text_parts[-1] + part) < 3500:
                    text_parts[-1] += "\n" + part
                else:
                    text_parts.append(part)

            translated_text = "\n".join([GoogleTranslator(source=source, target=abbr_languages[language]).translate(part) for part in text_parts])


        # Replace some terms
        translated_text = translated_text.replace("student", "learner")
        if language == "english":
            translated_text = translated_text.replace("lesson", "module").replace("score", "grade")

        if language == "greek":
            translated_text = re.sub(r'ΑΥΞΗΤΙΚΟΣ', 'augMENTOR', translated_text, flags=re.IGNORECASE)        
        elif language == "serbian":
            translated_text = re.sub(r'аугМЕНТОР', 'augMENTOR', translated_text, flags=re.IGNORECASE)
        elif language == "lithuanian":
            translated_text = re.sub(r'AUMENTORIUS', 'augMENTOR', translated_text, flags=re.IGNORECASE)

        # Some
        if "grade" in translated_text and language != "english":
            print("[WARNING] Google translation was not conducted correctly")
            translated_text = translation_model.run({"text": text, "language": language}).replace("```", "")
        
        return translated_text
    except Exception as e:
        print(f"[WARNING] Google translation failed.\n > {e}\nThe translation will be performed using LLM.") 
        return translation_model.run({"text": text, "language": language}).replace("```", "")