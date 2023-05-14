import random
import string
from pathlib import Path

from docxtpl import DocxTemplate

from app import db
from app.models import Threat, TechTactics


class Report:
    title = ''
    threat_sources = []
    objects_of_influence = []
    threats = []
    risks = []
    defence_class = ''
    threaters = []

    def init(self, title, threat_sources, objects_of_influence, threats, risks, threaters, defence_class):
        self.title = title
        self.threat_sources = threat_sources
        self.objects_of_influence = objects_of_influence
        self.threats = threats
        self.risks = risks
        self.threaters = threaters
        self.defence_class = defence_class


# из полного текста угроз получаем её имя
def remove_chars(s):
    return s.split(' Угроза', 1)[0]


def remove_char_list(list_t):
    threats = []
    for t in list_t:
        threats.append(remove_chars(t))

    return threats


def find_tt(threats):
    threats_tt = {}
    for t in threats:
        threat_query = db.session.query(Threat).filter(
            Threat.ubi_name == remove_chars(t)
        )
        threat = threat_query.first()
        tt = db.session.query(TechTactics).filter(
            TechTactics.threat_id == threat.id
        ).all()
        threat = threat_query.first()
        threats_tt.update({threat.text: tt})
    return threats_tt


def makefile(report):
    template = DocxTemplate(str(Path(Path.cwd(), 'template.docx')))

    context = {
        'threat_sources': report.threat_sources,
        'object_of_influence': report.objects_of_influence,
        'threats': report.threats,
        'risks': report.risks,
        'title': report.title,
        'threaters': report.threaters,
        'defence_class': report.defence_class,
        'tech_tactik': find_tt(report.threats),
        'short_threats': remove_char_list(report.threats)
    }

    template.render(context)
    report_name = ''.join(random.choices(string.ascii_lowercase, k=8)) + '_report.docx'
    template.save(str(Path(Path.cwd(), 'app','filestorage', report_name)))

    return 0
