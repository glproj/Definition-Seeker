from word_info_extractor import *
from programs import WORD_PRIMARY_CLASSES


def ipa(text: str, language: str):
    word_class = WORD_PRIMARY_CLASSES[language]
    word_list = re.sub(r"[.?;,!]", "", text).split()
    result = ""
    for word in word_list:
        try:
            if word:
                ipa_transcription = word_class(word.strip())
        except WordNotAvailable:
            result += word + ": not found\n"
            continue
        except Exception as e:
            print(word, e)
        result += word + ": " + ipa_transcription.ipa + "\n"
    return result


print(
    ipa(
        """la cigale, ayant chanté
      tout été,
  se trouva fort dépourvue
  quand la bise fut venue
  pas un seul petit morceau
  de mouche ou de vermisseau.""",
        language="fr",
    )
)
