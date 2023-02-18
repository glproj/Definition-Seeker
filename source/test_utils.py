from unittest import TestCase, main
from utils import *


class UtilsTestCase(TestCase):
    def test_get_examples(self):
        text = """Da ich mit der Geschwulst am Halse sehr geplagt war, indem Arzt und Chirurgus diese Exkreszenz erst vertreiben, hernach, wie sie sagten, zeitigen wollten, und sie zuletzt aufzuschneiden für gut befanden; so hatte ich eine geraume Zeit mehr an Unbequemlichkeit als an Schmerzen zu leiden, obgleich gegen das Ende der Heilung das immer fortdauernde Betupfen mit Höllenstein und andern ätzenden Dingen höchst verdrießliche Aussichten auf jeden neuen Tag geben mußte.


      Gewalt ist eher mit Gewalt zu vertreiben; aber ein gut gesinntes, zur Liebe und Teilnahme geneigtes Kind weiß dem Hohn und dem bösen Willen wenig entgegenzusetzen.


      Von euch Schurken keinen Spott!
    Ich tät euch Eseln eine Ehr an,
    Wie mein Vater Jupiter vor mir getan;
    Wollt eure dummen Köpf belehren
    Und euren Weibern die Mücken wehren,
    Die ihr nicht gedenkt ihnen zu vertreiben;
    So mögt ihr denn im Dreck bekleiben."""
        result = get_examples("vertreiben", text)
        self.assertEqual(len(result), 3)


if __name__ == "__main__":
    main()
