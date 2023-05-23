import calendar
import json
import os
import random
import string
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from docxtpl import DocxTemplate
from flask_login import current_user

from app import db, models
from app.models import Threat, TechTactics, ThreatSource, TypeOfNegativeConseq, TypeOfRisks

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
    kii = ''
    negative_conseq = []

    def init(self, title, threat_sources, objects_of_influence, threats, risks, threaters,
             defence_class, gis, ispdn, realiz, components, kii, negative_conseq):
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
        self.kii = kii
        self.negative_conseq = negative_conseq


class Threater:
    threater = ''
    threat_level = {}
    threat_point = {}
    category = ''

    def init(self, threater, threat_level, threat_point, category):
        self.threater = threater
        self.threat_level = threat_level
        self.threat_point = threat_point
        self.category = (category.replace("',)", '')).replace("('", "")  # убираем лишние символы


# из полного текста угроз получаем её имя
def remove_chars(s):
    return s.split(' Угроза', 1)[0]


def remove_char_list(list_t):
    threats = []
    for t in list_t:
        threats.append(remove_chars(t))
    return threats


# находим техники тактики
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
        threats_tt.update({str(threat.id) + ' - ' + threat.text: tt})
    return threats_tt


def merge_dicts(lst):
    res = {}
    for i in range(len(lst)):
        for k, v in lst[i].items():
            res[k] = res.get(k, '') + v
    return res


# получаем угрозы и их цели
def threaters(lst):
    lst = merge_dicts(lst)
    ph = "_уровень'"
    test = []
    for k, v in lst.items():
        if '-' not in v:
            if ph not in k:
                threat = Threater()
                category = db.session.query(ThreatSource.category).filter(
                    ThreatSource.object_name == k
                ).first()
                threat.init(k, lst[k + ph], lst[k], (str(category)))
                test.append(threat)
    return test


def findthreats(threats):
    threats_to_temp = []
    for t in threats:
        threat_query = db.session.query(Threat).filter(
            Threat.ubi_name == remove_chars(t)
        ).first()
        threats_to_temp.append(threat_query)
    return threats_to_temp


def findrisks(risks, negative):
    risks_neg = {}
    for r in risks:
        risks_db = db.session.query(TypeOfRisks.id).filter(
            TypeOfRisks.text == r
        )
        negative_cons = db.session.query(TypeOfNegativeConseq).filter(
            TypeOfNegativeConseq.typeId.in_(risks_db),
            TypeOfNegativeConseq.text.in_(negative)
        ).all()
        risks_neg.update({r: negative_cons})
    return risks_neg


def makefile(report):
    template = DocxTemplate(str(Path(Path.cwd(), 'template.docx')))
    context = {
        'threat_sources': report.threat_sources,
        'object_of_influence': report.objects_of_influence,
        'threats': findthreats(report.threats),
        'risks': report.risks,
        'title': report.title,
        'threaters': threaters(report.threaters),
        'defence_class': report.defence_class,
        'tech_tactik': find_tt(report.threats),
        'short_threats': remove_char_list(report.threats),
        'components': report.components,
        'gis': report.gis,
        'ispdn': report.ispdn,
        'realiz': report.realiz,
        'kii': report.kii,
        'negative_conseq': findrisks(report.risks, report.negative_conseq)
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
                          owner=current_user.name,
                          date=datetime.fromtimestamp(timestamp),
                          file=blob_file
                          )
        db.session.add(f)
        db.session.commit()
        print('файл ' + filename + ' сохранён успешно')
    except Exception as e:
        print('save_report', e)
        db.session.rollback()
    finally:
        db.session.close()
        os.remove(str(Path(folder_name_in, filename)))


def readreport(data, filename):
    with open(str(Path(folder_name_out, filename)), 'wb') as file:
        file.write(data)
    return folder_name_out
