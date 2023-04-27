#!flask/bin/python
from app import app, db
from app.models import Question, ThreatSource, ObjectOfInfluence, Threat, Option, SessionQuest, OptionConf, Result


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Question': Question, 'ThreatSource': ThreatSource, 'ObjectOfInfluence': ObjectOfInfluence, 'Threat': Threat, 'Option': Option,
            'SessionQuest': SessionQuest, 'OptionConf': OptionConf, 'Result': Result}