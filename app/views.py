import json
import traceback
from urllib.parse import urlparse, urljoin

from flask import render_template, request, redirect, url_for, send_from_directory
from flask import session as flask_session
from flask_login import login_required, login_user, current_user, logout_user

from app import app as app, login_manager
from app import db, models
from app.forms.LoginForm import LoginForm
from app.makefile import Report, makefile, save_report, readreport
from app.models import Question, Option, ObjectOfInfluence, OptionConf, User, \
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
@login_required
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
    #   проверка типа вопроса если с выбором то один шаблон если нет то другой
    if question[page].type == 'pick':
        template = "index.html"
    else:
        template = "QuestionConformity.html"
    if page == 0:
        flask_session['objects_of_influence'] = []
        flask_session['threater'] = []
        flask_session['threat_source'] = []
        flask_session['threat_source_level'] = []
        flask_session['type_of_risk'] = []
        flask_session['threats'] = []
        flask_session['type_of_negative'] = []
    # условие для третьего вопроса, выводит в него только нужные объекты воздействия
    if page == 2:
        flask_session['objects_of_influence'] = []
        req = request.form.to_dict()
        # object_inf_text = db.session.query(ObjectOfInfluence).filter(
        #     ObjectOfInfluence.object_name.in_(req.values())
        # )
        # object_inf = db.session.query(ObjectOfInfluence.id).filter(
        #     ObjectOfInfluence.object_name.in_(req.values())
        # )
        # comp = db.session.query(ComponentObjectOfInfluence.text).filter(
        #     ComponentObjectOfInfluence.ObjectOfInfluenceId.in_(object_inf)
        # )
        for k, r in req.items():
            flask_session['objects_of_influence'].append(r)
        # components = OptionConfs.query.filter(
        #     OptionConfs.option_conf_1.in_(comp)
        # ).all()
        if not flask_session.modified:
            flask_session.modified = True
        # option_confs = components
        # options = object_inf_text.all()
        template = "in_work.html"
    if page == 3:
        pass
    if page == 4:
        #   сохраняем результаты предыдущего вопроса в flask_session
        flask_session['threater'] = []
        req = request.form.to_dict()
        for k, r in req.items():
            flask_session['threater'].append({k: r})
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
        flask_session['threat_source_level'] = []
        ph = "_уровень"
        for k, r in req.items():
            if ph not in k:
                flask_session['threat_source'].append(r)
            else:
                flask_session['threat_source_level'].append(r)

            if not flask_session.modified:
                flask_session.modified = True
        print(flask_session['threat_source'])
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
        req = request.form.to_dict()
        # сохраняем негативные последсвтия
        flask_session['type_of_negative'] = [v for (k, v) in req.items()]
        threats_picked = []
        # словарь с уровнями
        threat_level = {'H1': 'низким', 'H2': 'низким', 'H3': 'средним', 'H4': 'высоким'}
        #   из базы данных выбираем объекты возд которые пользователь выбрал в 3 вопросе
        object_inf = db.session.query(ObjectOfInfluence.id).filter(
            ObjectOfInfluence.object_name.in_(flask_session['objects_of_influence']))
        #   из базы получаем компоненты для всех выбранных объектов воздействия
        component_obj = db.session.query(ComponentObjectOfInfluence).filter(
            ComponentObjectOfInfluence.ObjectOfInfluenceId.in_(object_inf)
        ).all()
        #   доводим списки для необходимой нам длинны
        threat_source = flask_session['threat_source'] * len(component_obj)
        threat_source_level = flask_session['threat_source_level'] * len(component_obj)
        #   запускаем цикл по 3 спискам: компоненты, объекты возд, уровень объектов возд
        for t, o, l in zip(threat_source, component_obj, threat_source_level):
            threat_db = db.session.query(Threat).filter(
                Threat.ObjectOfInfluence.ilike("%" + o.text + "%"), Threat.ThreatSource
                .ilike("%" + threat_level[l] + "%"), Threat.ThreatSource.ilike("%" + t + "%")
            ).all()
            if len(threat_db) > 0:
                threats_picked.extend(threat_db)
        #   удаляем повторки
        visited = set()
        threats_picked[:] = [x for x in threats_picked if x not in visited and not visited.add(x)]
        # сортируем угрозы по возрастанию id
        threats_picked.sort(key=lambda x: x.id)
        # кладём в переменную для шаблона
        options_list = threats_picked
    if page == 8:
        flask_session['threats'] = []
        req = request.form.to_dict()
        for k, v in req.items():
            flask_session['threats'].append(v)
        options = [k + ' - ' + v.replace("'", "") for (k, v) in req.items()]
        option_confs = db.session.query(OptionConfs).filter(OptionConfs.question_id == 9).all()
    # возращаем html шаблон и переменные которые будут в нём использоваться
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
@login_required
def set_result():
    req_params = request.get_json('/quest/result', silent=True)  # принимаем результаты в формате json
    if req_params is not None:
        print('ls', req_params)
        # print(req_params.get('data', '').get('4', ''))
        # print('gis', req_params.get('data', '').get('ГИС_знач', ''))
        # print('ispdn', req_params.get('data', '').get('ispdn', ''))
        # print('realiz', req_params.get('data', '').get('8', ''))
        # print(type(req_params.get('data', '').get('8', '')))
        # print(flask_session['threater'])
        report = Report()
        report.init('Отчёт',
                    flask_session['threat_source'],
                    flask_session['objects_of_influence'],
                    threats=flask_session['threats'],
                    risks=flask_session['type_of_risk'],
                    threaters=flask_session['threater'],
                    ispdn=req_params.get('data', '').get('ispdn', ''),
                    gis=req_params.get('data', '').get('ГИС_знач', ''),
                    realiz=json.loads(req_params.get('data', '').get('8', '')),
                    defence_class='',
                    components=req_params.get('data', '').get('4', ''),
                    kii=req_params.get('data', '').get('kii_level', ''),
                    negative_conseq=flask_session['type_of_negative']
                    )
        try:
            filename = makefile(report)
            save_report(filename)
        except Exception as e:
            print(traceback.format_exc())

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
    flask_session.clear()
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
            u: User = models.User(name=newuser.name, password=newuser.password)  # type: ignore
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
            models.Report.name == filename,
            models.Report.owner == current_user.name
        ).first()
    else:
        file = models.Report.query.filter(
            models.Report.owner == current_user.name,
        ).order_by(models.Report.date.desc()).limit(1).first()
    download_string = readreport(file.file, file.name)
    return send_from_directory(download_string, file.name)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/docs")
@login_required
def docx():
    return render_template("docs.html")
