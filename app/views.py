import json
from urllib.parse import urlparse, urljoin

from flask import render_template, request, redirect, url_for, send_from_directory
from flask import session as flask_session
from flask_login import login_required, login_user, current_user, logout_user

from app import app as app, login_manager
from app import db, models
from app.forms.LoginForm import LoginForm, RegistrationForm
from app.makefile import Report, makefile, save_report, readreport
from app.models import Question, Option, ObjectOfInfluence, OptionConf, Result, User, \
    ComponentObjectOfInfluence, OptionConfs, Threat, TypeOfNegativeConseq, TypeOfRisks



def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


@app.route('/quest/>', methods=['GET', 'POST'])
@app.route('/quest/<int:page>', methods=['GET', 'POST'])
# @login_required
def quest(page):
    print(page, request.form.to_dict())
    threats = []
    question = Question.query.order_by(Question.question_number.asc()).all()
    options_list = Option.query.filter(
        Option.question_id == question[page].id
    ).all()
    options = OptionConf.query.filter(
        OptionConf.question_id == question[page].id
    ).all()
    option_confs = OptionConfs.query.filter(
        OptionConfs.question_id == question[page].id
    ).all()
    if question[page].type == 'pick':
        template = "index.html"
    else:
        template = "QuestionConformity.html"
    if page == 1:
        pass
    # условие для третьего вопроса, выводит в него только нужные объекты воздействия
    if page == 2:
        flask_session.clear()
        flask_session['objects_of_influence'] = []
        req = request.form.to_dict()
        object_inf_text = object_inf = db.session.query(ObjectOfInfluence).filter(
            ObjectOfInfluence.object_name.in_(req.values())
        )
        object_inf = db.session.query(ObjectOfInfluence.id).filter(
            ObjectOfInfluence.object_name.in_(req.values())
        )
        comp = db.session.query(ComponentObjectOfInfluence.text).filter(
            ComponentObjectOfInfluence.ObjectOfInfluenceId.in_(object_inf)
        )
        for k, r in req.items():
            flask_session['objects_of_influence'].append(r)

        components = OptionConfs.query.filter(
            OptionConfs.option_conf_1.in_(comp)
        ).all()
        if not flask_session.modified:
            flask_session.modified = True
        option_confs = components
        options = object_inf_text.all()
    if page == 3:
        if not flask_session.modified:
            flask_session.modified = True
    if page == 4:
        #   сохраняем результаты предыдущего вопроса в flask_session
        flask_session['threater'] = []
        req = request.form.to_dict()
        for k, r in req.items():
            flask_session['threater'].append(k + ' : ' + r)
        #   условие для 4 вопроса выводит только нужные объекты воздействия
        object_inf = db.session.query(OptionConf).filter(
            OptionConf.text.in_(flask_session['objects_of_influence']), OptionConf.question_id == 5)

        option_confs_db = db.session.query(OptionConfs).filter(
            OptionConfs.question_id == 5
        )
        options = object_inf.all()
        option_confs = option_confs_db.all()
    if page == 5:
        req = request.form.to_dict()
        flask_session['threat_source'] = []
        for k, r in req.items():
            flask_session['threat_source'].append(r)
            if not flask_session.modified:
                flask_session.modified = True
    if page == 6:
        req = request.form.to_dict()
        flask_session['type_of_risk'] = []
        flask_session['type_of_risk'] = [v for (k, v) in req.items()]
        if not flask_session.modified:
            flask_session.modified = True
        risks = db.session.query(TypeOfRisks.id).filter(
            TypeOfRisks.text.in_(flask_session['type_of_risk'])
        )
        type_of_neg_cons = db.session.query(TypeOfNegativeConseq).filter(
            TypeOfNegativeConseq.typeId.in_(risks)
        ).all()
        options_list = type_of_neg_cons
    if page == 7:
        threats_picked = []
        threat_level = {'H1': 'низким', 'H2': 'низким', 'H3': 'средним', 'H4': 'высоким'}
        print('objects_of_influence', flask_session['objects_of_influence'])
        print('threat_source', flask_session['threat_source'])

        for t, o in zip(flask_session['threat_source'], flask_session['objects_of_influence']):
            threat_db = db.session.query(Threat).filter(
                Threat.ObjectOfInfluence.ilike("%" + o + "%"), Threat.ThreatSource
                .ilike("%" + t + "%")
            ).all()
            if len(threat_db) > 0:
                threats_picked.extend(threat_db)
        options_list = threats_picked

    if page == 8:
        flask_session['threats'] = []
        req = request.form.to_dict()
        for k, v in req.items():
            flask_session['threats'].append(v)
        options = [v.replace("'", "") for (k, v) in req.items()]
        option_confs = db.session.query(OptionConfs).filter(OptionConfs.question_id == 9).all()

    return render_template(template,
                           QuestionForm=question,
                           Options=options_list,
                           PageNumber=page,
                           options_conf_text=options,
                           option_confs=option_confs,
                           Threats=threats,
                           Questionslength=len(question),
                           )


@app.route('/editor/', methods=['GET', 'POST'])
@app.route('/editor/add_quest', methods=['GET', 'POST'])  # добавление вопросов
@login_required
def editor():
    if request.method == 'POST':
        try:
            text_q = request.form.get("text")
            type_q = request.form.get("type")
            q = models.Question(text=text_q, type=type_q)
            db.session.add(q)
            db.session.commit()
        except:
            db.session.rollback()
        finally:
            db.session.close()

    return render_template('editor.html',
                           questions=models.Question.query.all(),
                           options=models.Option.query.all())


@app.route('/editor/add_option', methods=['GET', 'POST'])  # добавление ответов
@login_required
def editor_option():
    if request.method == 'POST':
        try:
            text_o = request.form.get("text_o")
            quest_num = request.form.get("question_id")
            o = models.Option(text=text_o, question_id=int(quest_num))
            db.session.add(o)
            db.session.commit()
        except:
            db.session.rollback()
        finally:
            db.session.close()

    return render_template('editor.html',
                           questions=models.Question.query.all(),
                           options=models.Option.query.all())


@app.route('/quest/result', methods=['GET', 'POST'])
def set_result():
    req_params = request.get_json('/quest/result', silent=True)  # принимаем результаты в формате json
    print('ls', req_params)
    report = Report()
    report.init('Отчёт',
                flask_session['threat_source'],
                flask_session['objects_of_influence'],
                flask_session['threats'],
                flask_session['type_of_risk'],
                flask_session['threater'],
                )
    #ispdn = req_params['ispdn'],
    #gis = req_params['ГИС_знач'],
    #realiz = req_params['8']

    filename = makefile(report)
    save_report(filename)

    return render_template('result.html')


@app.route('/login', defaults={'errors': None}, methods=['GET', 'POST'])
@app.route('/login/<errors>')
def login(errors=None):
    form = LoginForm()
    return render_template('login.html', title='Вход', form=form, error=errors)


@app.route('/')
@app.route('/main')
@login_required
def main_page():
    return render_template('main_page.html')


@app.route('/check_login', methods=['GET', 'POST'])
def check_login():
    if request.method == 'POST':
        name = request.form.get('username')
        password = request.form.get('password')
        auth = User.query.filter(
            User.name == name
        ).first()
        if auth is not None and auth.check_password(password):
            login_user(auth)
            return redirect(url_for('main_page'))
        else:
            return redirect(url_for('login', errors="Неверный логин или пароль"))


@app.route('/register', methods=['GET', 'POST'])
def register_form():
    form = request.form.to_dict()
    if form is not None:
        try:
            newuser = User()
            newuser.name = form['username']
            newuser.set_password(form['password'])
            newuser.UUID = 'str(uuid0.generate())'
            u: User = models.User(name=newuser.name, password=newuser.password, UUID=newuser.UUID)  # type: ignore
            db.session.add(u)
            db.session.commit()
            return redirect(url_for('main_page'))
        except Exception as e:
            print(e)
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/personal_account')
@login_required
def personal_account():
    user_reports = models.Report.query.filter(
        models.Report.owner == current_user.name
    ).all()
    user = current_user
    return render_template('personal_account.html', user=user, reports=user_reports)

@app.route('/download')
@app.route('/download/<filename>')
@login_required
def download(filename=None):
    if filename is not None:
        file = models.Report.query.filter(
            models.Report.name == filename
        ).first()
    else:
        file = models.Report.query.filter(
            models.Report.owner == 'test',
        ).order_by(models.Report.date.desc()).limit(1).first()
    download_string = readreport(file.file, file.name)
    return send_from_directory(download_string, file.name)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
