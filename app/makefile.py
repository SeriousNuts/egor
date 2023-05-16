import calendar
import os
import random
import string
import time
from datetime import datetime
from pathlib import Path

from docxtpl import DocxTemplate
from flask_login import current_user

from app import db, models
from app.models import Threat, TechTactics

#   каталог для загружаемых файлов
folder_name_in = str(Path(Path.cwd(), 'app', 'filestorage'))
#   каталог для скачиваемых файлов
folder_name_out = str(Path(Path.cwd(), 'app', 'filestorageOUT'))


class Report:
    title = ''
    threat_sources = []
    objects_of_influence = []
    threats = []
    risks = []
    defence_class = ''
    threaters = []
    gis = ''
    ispdn = ''
    realiz = {}
    components = {}

    def init(self, title, threat_sources, objects_of_influence, threats, risks, threaters,
             defence_class, gis, ispdn, realiz, components):
        self.title = title
        self.threat_sources = threat_sources
        self.objects_of_influence = objects_of_influence
        self.threats = threats
        self.risks = risks
        self.threaters = threaters
        self.defence_class = defence_class
        self.gis = gis
        self.ispdn = ispdn
        self.realiz = realiz
        self.components = components


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
        'short_threats': remove_char_list(report.threats),
        'components': report.components,
        'gis': report.gis,
        'ispdn': report.ispdn,
        'realiz': report.realiz
    }


    template.render(context)
    report_name = ''.join(random.choices(string.ascii_lowercase, k=8)) + '_report.docx'
    template.save(str(Path(Path.cwd(), 'app', 'filestorage', report_name)))
    return report_name


def save_report(filename):
    timestamp = calendar.timegm(time.gmtime())
    with open(str(Path(folder_name_in, filename)), 'rb') as file:
        # записываем в формат blob
        blob_file = file.read()
    try:
        f = models.Report(name=filename,
                          desc='потом будем его формировать',
                          owner='test',
                          date=datetime.fromtimestamp(timestamp),
                          file=blob_file
                          )
        db.session.add(f)
        db.session.commit()
        print('файл ' + filename + ' сохранён успешно')
    except Exception as e:
        print(e)
        db.session.rollback()
    finally:
        db.session.close()
        os.remove(str(Path(folder_name_in, filename)))


def readreport(data, filename):
    with open(str(Path(folder_name_out, filename)), 'wb') as file:
        file.write(data)
    return folder_name_out
