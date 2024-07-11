from deep_translator import GoogleTranslator

abbr_languages = {'English':'en', 'Greek':'el', 'Serbian': 'sr', 'Lithuanian': 'lt'}
def translate(text:str=None, language:str=None):
    '''
        Translate text and replace some terms

        Parameters
        ----------
        text: (str)
            input text

        Return
        ------
        processed text (str)

    '''
    if len(text) < 4000:
        translated_text = GoogleTranslator(source='auto', target=language).translate(text)
    else:
        # Split text in parts
        text_parts = [ "" ]
        for part in text.split("\n"):
            if len(part) > 4500: raise Exception("Text cannot be translated")

            if len(text_parts[-1] + part) < 4500:
                text_parts[-1] += "\n" + part
            else:
                text_parts.append(part)

        translated_text = "\n".join([GoogleTranslator(source='auto', target=language).translate(part) for part in text_parts])


    # Replace some terms
    if language == "en":
        translated_text = translated_text.replace("student", "learner").replace("lesson", "module").replace("score", "grade")

    return translated_text