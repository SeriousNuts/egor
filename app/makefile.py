import random
import string
from pathlib import Path

from docxtpl import DocxTemplate


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


def makefile(report):
    template = str(Path(Path.cwd(), 'template.docx'))

    context = {
        'threat_sources': report.threat_sources,
        'object_of_influence': report.objects_of_influence,
        'threats': report.threats,
        'risks': report.risks,
        'title': report.title,
        'threaters': report.threaters,
        'defence_class': report.defence_class
    }

    template.render(context)
    report_name = ''.join(random.choices(string.ascii_lowercase, k=8)) + '_report.xlsx'
    template.save(str(Path(Path.cwd(), report_name)))

    return 0
