import os
from flask import Flask, redirect, url_for, session, render_template, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user, LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask import current_app


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  #16MB max-limit


db = SQLAlchemy(app)
login_manager =LoginManager(app)
login_manager.login_view='login'


#criar usuario
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    imagem = db.Column(db.String(200), nullable=True)
    projetos = db.relationship('Projeto', backref='usuario', lazy=True)

#criar tabela
class Projeto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_projeto = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.String(250), nullable=False)
    status = db.Column(db.String(50),nullable=False)
    imagem = db.Column(db.String(200), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        senha_hash = generate_password_hash(senha)
        user = Usuario(usuario=usuario, senha=senha_hash)
        db.session.add(user)
        db.session.commit()
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('login'))
    return render_template('registrar.html')
    

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))
    print(f"Carregando usuário: {user}")
    return user

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        user= Usuario.query.filter_by(usuario=usuario).first()
        if user:
            print(f"Usuário encontrado: {user.usuario}")
        else:
             print("Usuário não encontrado.")
        if user and check_password_hash(user.senha, senha):
            print("Senha verificada com sucesso.")
            session['usuario_id']=user.id
            session['usuario'] =user.usuario
            login_user(user)
            flash('Seja bem Vindo !', 'success')
            return redirect(url_for('admin'))
        flash('Usuário ou senha incorretos.', 'error')
    return render_template('login.html')
    #return 'Login'

@app.route('/logout')
def logout():
    session.clear()  # Limpa todos os dados da sessão
    flash('Você saiu da sua conta com sucesso.', 'success')
    return redirect(url_for('home'))  # Redireciona para a página de home

@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html')


    
@app.route('/projetos')
def projetos():
    projeto = Projeto.query.all()  # Recupera todos os projetos
    return render_template('projetos.html', projetos = projeto)



@app.route('/adicionar_projeto', methods=['GET', 'POST'])
def adicionar_projeto():
    if request.method == 'POST':
        projeto_nome = request.form['projeto_nome']
        descricao = request.form['descricao']
        imagem = request.files['imagem']

        # Salvando a imagem como discutido anteriormente
        if imagem:
            imagem_filename = secure_filename(imagem.filename)
            upload_path = os.path.join(current_app.root_path, 'static/uploads', imagem_filename)
            imagem.save(upload_path)
        else:
            imagem_filename = ''

        # Obtenha o ID do usuário atual
        current_id = current_user.id

        # Verifique se current_id não é None
        if current_id is None:
            flash('Erro: Usuário não autenticado.', 'error')
            return redirect(url_for('login'))

        novo_projeto = Projeto(
            nome_projeto=projeto_nome,
            descricao=descricao,
            status='Novo',
            imagem=imagem_filename,
            usuario_id=current_id
        )

        db.session.add(novo_projeto)
        db.session.commit()
        flash('Projeto adicionado com sucesso', 'success')
        return redirect(url_for('projetos'))
    return render_template('adicionar_projetos.html')


@app.route('/editar_projeto/<int:projeto_id>', methods=['GET', 'POST'])
def editar_projeto(projeto_id):
    projeto = Projeto.query.get_or_404(projeto_id)
    if projeto.usuario_id != current_user.id:
        flash('Você não tem permissão para editar este projeto.', 'error')
        return redirect(url_for('projetos'))

    if request.method == 'POST':
        projeto.nome_projeto = request.form['projeto_nome']
        projeto.descricao = request.form['descricao']
        projeto.status = request.form['status']

        imagem = request.files.get('imagem')
        if imagem and imagem.filename:
            imagem_filename = secure_filename(imagem.filename)
            upload_path = os.path.join(current_app.root_path, 'static/uploads', imagem_filename)
            imagem.save(upload_path)
            projeto.imagem = imagem_filename
        db.session.commit()
        flash('Projeto editado com sucesso', 'success')
        return redirect(url_for('projetos'))
    return render_template('editar_projeto.html', projeto=projeto)


@app.route('/deletar_projeto/<int:projeto_id>', methods=['GET', 'POST'])
def deletar_projeto(projeto_id):
    try:
        projeto = Projeto.query.get_or_404(projeto_id)     
        if projeto.usuario_id != current_user.id:
            return redirect(url_for('projetos'))
        
            # Deletar a imagem associada ao projeto, se existir
        if projeto.imagem:
            caminho_imagem = os.path.join(current_app.root_path, 'static/uploads', projeto.imagem)
            if os.path.exists(caminho_imagem):
                os.remove(caminho_imagem)
        
        db.session.delete(projeto)
        db.session.commit()
        flash('Projeto deletado com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar o projeto: {str(e)}', 'error')

    return redirect(url_for('projetos'))
    
@app.route('/contatos')
def contatos():
    return render_template('contatos.html')


if __name__ =="__main__":
    with app.app_context():
        db.create_all() 
        app.run(debug=True)

