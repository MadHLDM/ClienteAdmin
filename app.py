#!/usr/bin/env python3
import io
import os
import re
import json
import html
import urllib.parse
from datetime import date, datetime, timedelta
from typing import Dict, Tuple, Optional

from db import (
    init_db,
    get_db,
    fetch_clients,
    fetch_client_by_id,
    insert_client,
    update_client,
    delete_client,
    fetch_income_stats,
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")


def read_file(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def render_page(title: str, body_html: str, messages: Optional[Dict[str, str]] = None) -> bytes:
    base_path = os.path.join(TEMPLATES_DIR, "base.html")
    base = read_file(base_path).decode("utf-8")
    flash_html = ""
    if messages:
        for level, msg in messages.items():
            flash_html += f'<div class="flash {html.escape(level)}">{html.escape(msg)}</div>'
    out = base.replace("{{ title }}", html.escape(title))
    out = out.replace("{{ flash }}", flash_html)
    out = out.replace("{{ body }}", body_html)
    return out.encode("utf-8")


def parse_post(environ) -> Dict[str, str]:
    try:
        size = int(environ.get('CONTENT_LENGTH') or 0)
    except (ValueError, TypeError):
        size = 0
    data = environ['wsgi.input'].read(size) if size > 0 else b""
    ctype = environ.get('CONTENT_TYPE', '')
    if 'application/x-www-form-urlencoded' in ctype:
        return {k: v[0] for k, v in urllib.parse.parse_qs(data.decode('utf-8')).items()}
    return {}


def http_redirect(start_response, location: str):
    start_response('302 Found', [('Location', location)])
    return [b'']


def not_found(start_response):
    start_response('404 Not Found', [('Content-Type', 'text/plain; charset=utf-8')])
    return [b'Not Found']


def static_app(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    rel = path[len('/static/'):]
    fs_path = os.path.normpath(os.path.join(STATIC_DIR, rel))
    if not fs_path.startswith(STATIC_DIR) or not os.path.exists(fs_path):
        return not_found(start_response)
    if fs_path.endswith('.css'):
        ctype = 'text/css; charset=utf-8'
    elif fs_path.endswith('.js'):
        ctype = 'application/javascript; charset=utf-8'
    elif fs_path.endswith('.png'):
        ctype = 'image/png'
    elif fs_path.endswith('.jpg') or fs_path.endswith('.jpeg'):
        ctype = 'image/jpeg'
    elif fs_path.endswith('.svg'):
        ctype = 'image/svg+xml; charset=utf-8'
    else:
        ctype = 'application/octet-stream'
    start_response('200 OK', [('Content-Type', ctype)])
    return [read_file(fs_path)]


def safe_date(s: str) -> Optional[date]:
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def format_currency(value: Optional[float]) -> str:
    if value is None:
        return "—"
    integer = int(round(value))
    s = f"{integer:,}".replace(",", ".")
    return f"R$ {s}"


def income_class(value: Optional[float]) -> Optional[str]:
    if value is None:
        return None
    if value <= 980.00:
        return 'A'
    if 980.00 < value <= 2500.00:
        return 'B'
    return 'C'


def cpf_is_valid(cpf: str) -> bool:
    # Regra solicitada: CPF com 10 dígitos (somente números)
    return bool(re.fullmatch(r"\d{10}", cpf))


# Nome: apenas letras (com acentos), espaço, apóstrofo (' ou ’), hífen (-) e ponto (.)
NAME_REGEX = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ'’\.\- ]{1,150}$")


def clients_list(environ, start_response):
    qs = urllib.parse.parse_qs(environ.get('QUERY_STRING', ''))
    q = (qs.get('q') or [''])[0].strip()
    rows = fetch_clients(q)
    today_str = date.today().isoformat()
    html_rows = []
    for r in rows:
        badge = ''
        cls = income_class(r['renda_familiar'])
        label = format_currency(r['renda_familiar'])
        if cls is None:
            badge = f'<span class="badge-income badge-neutral">{html.escape(label)}</span>'
        else:
            badge = f'<span class="badge-income badge-{cls.lower()}">{html.escape(label)}</span>'
        html_rows.append(
            f"""
            <tr>
                <td>{html.escape(r['nome'])}</td>
                <td class=\"col-income\">{badge}</td>
                <td class=\"col-actions\">
                    <a class=\"btn btn-secondary\" href=\"/clients/{r['id']}/edit\">Editar</a>
                    <form method=\"post\" action=\"/clients/{r['id']}/delete\" style=\"display:inline-block\"> 
                        <button class=\"btn btn-danger\" type=\"submit\" data-confirm=\"Excluir este cliente?\">Excluir</button>
                    </form>
                </td>
            </tr>
            """
        )
    body = f"""
    <div class=\"page-header\">
        <h1>Clientes</h1>
        <div class=\"actions\">
            <a class=\"btn btn-primary\" href=\"/clients/new\">Novo Cliente</a>
        </div>
    </div>
    <form class=\"search\" method=\"get\" action=\"/clients\">
        <input type=\"text\" name=\"q\" value=\"{html.escape(q)}\" placeholder=\"Pesquisar por nome...\" maxlength=\"150\" />
        <button class=\"btn\" type=\"submit\">Pesquisar</button>
    </form>
    <table class=\"table\">
        <thead><tr><th>Nome</th><th>Renda</th><th></th></tr></thead>
        <tbody>
            {''.join(html_rows) or '<tr><td colspan=3 class=\'empty\'>Nenhum cliente encontrado.</td></tr>'}
        </tbody>
    </table>
    """
    start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
    return [render_page("Clientes", body)]


def client_form(environ, start_response, client=None, errors: Optional[Dict[str, str]] = None):
    is_edit = client is not None
    action = f"/clients/{client['id']}/update" if is_edit else "/clients"
    nome = client['nome'] if is_edit else ''
    cpf = client['cpf'] if is_edit else ''
    data_nascimento = client['data_nascimento'] if is_edit else ''
    data_cadastro = client['data_cadastro'] if is_edit else date.today().isoformat()
    renda = '' if (not is_edit or client['renda_familiar'] is None) else f"{client['renda_familiar']:.2f}"
    today_str = date.today().isoformat()
    err_html = ''
    if errors:
        items = ''.join(f"<li><strong>{html.escape(k)}</strong>: {html.escape(v)}</li>" for k, v in errors.items())
        err_html = f"<div class=\"errors\"><ul>{items}</ul></div>"
    body = f"""
    <div class=\"page-header\">
        <h1>{'Editar' if is_edit else 'Novo'} Cliente</h1>
        <div class=\"actions\">
            <a class=\"btn\" href=\"/clients\">Voltar</a>
        </div>
    </div>
    {err_html}
    <form class=\"form\" method=\"post\" action=\"{action}\"> 
        <div class=\"field\">
            <label>Nome</label>
            <input type=\"text\" name=\"nome\" value=\"{html.escape(nome)}\" required maxlength=\"150\" pattern=\"^[A-Za-zÀ-ÖØ-öø-ÿ'’. -]{{1,150}}$\" autocomplete=\"name\" placeholder=\"Nome completo\" />
            <small>Permite letras, espaços, apóstrofo, hífen e ponto.</small>
        </div>
        <div class=\"field\">
            <label>CPF</label>
            <input type=\"text\" name=\"cpf\" value=\"{html.escape(cpf)}\" required pattern=\"\\d{{10}}\" maxlength=\"10\" inputmode=\"numeric\" placeholder=\"Somente números\" />
            <small>Digite 10 dígitos (somente números).</small>
        </div>
        <div class=\"field\">
            <label>Data de nascimento</label>
            <input type=\"date\" name=\"data_nascimento\" value=\"{html.escape(data_nascimento)}\" required max=\"{today_str}\" lang=\"pt-BR\" placeholder=\"dd/mm/aaaa\" />
        </div>
        <div class=\"field\">
            <label>Data de cadastro</label>
            <input type=\"date\" name=\"data_cadastro\" value=\"{html.escape(data_cadastro)}\" readonly lang=\"pt-BR\" placeholder=\"dd/mm/aaaa\" />
        </div>
        <div class=\"field\">
            <label>Renda familiar</label>
            <input type=\"number\" step=\"0.01\" min=\"0\" name=\"renda_familiar\" value=\"{html.escape(renda)}\" placeholder=\"Opcional\" />
        </div>
        <div class=\"form-actions\">
            <button class=\"btn btn-primary\" type=\"submit\">Salvar</button>
        </div>
    </form>
    """
    start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
    return [render_page('Cliente', body)]


def clients_create(environ, start_response):
    form = parse_post(environ)
    errors = {}
    nome = (form.get('nome') or '').strip()
    nome = re.sub(r"\s+", " ", nome)
    cpf = (form.get('cpf') or '').strip()
    data_nascimento = (form.get('data_nascimento') or '').strip()
    data_cadastro = (form.get('data_cadastro') or '').strip() or date.today().isoformat()
    renda_raw = (form.get('renda_familiar') or '').strip()
    renda = None
    if not nome:
        errors['Nome'] = 'Campo obrigatório.'
    if len(nome) > 150:
        errors['Nome'] = 'Máximo 150 caracteres.'
    elif not NAME_REGEX.fullmatch(nome):
        errors['Nome'] = "Use apenas letras, espaços, apóstrofo, hífen e ponto."
    if not cpf or not re.fullmatch(r"\d{10}", cpf):
        errors['CPF'] = 'Informe 10 dígitos numéricos.'
    elif not cpf_is_valid(cpf):
        errors['CPF'] = 'CPF inválido.'
    dn = safe_date(data_nascimento)
    if not dn:
        errors['Data de nascimento'] = 'Data inválida ou vazia.'
    elif dn > date.today():
        errors['Data de nascimento'] = 'Não pode ser futura.'
    dc = safe_date(data_cadastro) or date.today()
    if renda_raw:
        try:
            renda = float(renda_raw)
            if renda < 0:
                errors['Renda familiar'] = 'Deve ser maior ou igual a 0.'
        except ValueError:
            errors['Renda familiar'] = 'Valor inválido.'
    if errors:
        return client_form(environ, start_response, None, errors)
    ok, err = insert_client(nome, cpf, dn.isoformat(), dc.isoformat(), renda)
    if not ok:
        return client_form(environ, start_response, None, {'CPF': err})
    return http_redirect(start_response, "/clients")


def clients_update(environ, start_response, client_id: int):
    client = fetch_client_by_id(client_id)
    if not client:
        return not_found(start_response)
    form = parse_post(environ)
    errors = {}
    nome = (form.get('nome') or '').strip()
    nome = re.sub(r"\s+", " ", nome)
    cpf = (form.get('cpf') or '').strip()
    data_nascimento = (form.get('data_nascimento') or '').strip()
    data_cadastro = client['data_cadastro']  # keep original
    renda_raw = (form.get('renda_familiar') or '').strip()
    renda = None
    if not nome:
        errors['Nome'] = 'Campo obrigatório.'
    if len(nome) > 150:
        errors['Nome'] = 'Máximo 150 caracteres.'
    elif not NAME_REGEX.fullmatch(nome):
        errors['Nome'] = "Use apenas letras, espaços, apóstrofo, hífen e ponto."
    if not cpf or not re.fullmatch(r"\d{10}", cpf):
        errors['CPF'] = 'Informe 10 dígitos numéricos.'
    elif not cpf_is_valid(cpf):
        errors['CPF'] = 'CPF inválido.'
    dn = safe_date(data_nascimento)
    if not dn:
        errors['Data de nascimento'] = 'Data inválida ou vazia.'
    elif dn > date.today():
        errors['Data de nascimento'] = 'Não pode ser futura.'
    if renda_raw:
        try:
            renda = float(renda_raw)
            if renda < 0:
                errors['Renda familiar'] = 'Deve ser maior ou igual a 0.'
        except ValueError:
            errors['Renda familiar'] = 'Valor inválido.'
    if errors:
        client['nome'] = nome
        client['cpf'] = cpf
        client['data_nascimento'] = data_nascimento
        client['renda_familiar'] = renda
        return client_form(environ, start_response, client, errors)
    ok, err = update_client(client_id, nome, cpf, dn.isoformat(), data_cadastro, renda)
    if not ok:
        return client_form(environ, start_response, client, {'CPF': err})
    return http_redirect(start_response, "/clients")


def clients_delete(environ, start_response, client_id: int):
    delete_client(client_id)
    return http_redirect(start_response, "/clients")


def reports(environ, start_response):
    qs = urllib.parse.parse_qs(environ.get('QUERY_STRING', ''))
    period = (qs.get('period') or ['month'])[0]
    today = date.today()
    if period == 'today':
        start_dt = today
    elif period == 'week':
        start_dt = today - timedelta(days=today.weekday())
    elif period == 'month':
        start_dt = today.replace(day=1)
    else:
        start_dt = date(1970, 1, 1)
    stats = fetch_income_stats(start_dt.isoformat())
    # Cards
    body = f"""
    <div class=\"page-header\">
        <h1>Relatórios</h1>
        <div class=\"actions\"><a class=\"btn\" href=\"/clients\">Clientes</a></div>
    </div>
    <form class=\"filters\" method=\"get\" action=\"/reports\">
        <label>Período</label>
        <select name=\"period\" onchange=\"this.form.submit()\">
            <option value=\"today\" {'selected' if period=='today' else ''}>Hoje</option>
            <option value=\"week\" {'selected' if period=='week' else ''}>Esta semana</option>
            <option value=\"month\" {'selected' if period=='month' else ''}>Este mês</option>
            <option value=\"all\" {'selected' if period=='all' else ''}>Todos</option>
        </select>
    </form>
    <div class=\"cards\">
        <div class=\"card\">
            <div class=\"card-title\">Maiores de 18 com renda > média</div>
            <div class=\"card-value\">{stats['over_18_above_avg']}</div>
            <div class=\"card-note\">Média geral: {format_currency(stats['avg_income'])}</div>
        </div>
        <div class=\"card\">
            <div class=\"card-title\">Classe A</div>
            <div class=\"card-value\">{stats['class_a']}</div>
        </div>
        <div class=\"card\">
            <div class=\"card-title\">Classe B</div>
            <div class=\"card-value\">{stats['class_b']}</div>
        </div>
        <div class=\"card\">
            <div class=\"card-title\">Classe C</div>
            <div class=\"card-value\">{stats['class_c']}</div>
        </div>
    </div>
    """
    start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
    return [render_page('Relatórios', body)]


def route(environ) -> Tuple[str, Optional[int]]:
    path = environ.get('PATH_INFO', '/')
    if path == '/':
        return 'root', None
    if path.startswith('/static/'):
        return 'static', None
    if path == '/clients' and environ['REQUEST_METHOD'] == 'GET':
        return 'clients_list', None
    if path == '/clients' and environ['REQUEST_METHOD'] == 'POST':
        return 'clients_create', None
    if path == '/clients/new' and environ['REQUEST_METHOD'] == 'GET':
        return 'clients_new', None
    if path.startswith('/clients/') and path.endswith('/edit'):
        try:
            cid = int(path.split('/')[2])
            return 'clients_edit', cid
        except Exception:
            return '404', None
    if path.startswith('/clients/') and path.endswith('/update') and environ['REQUEST_METHOD'] == 'POST':
        try:
            cid = int(path.split('/')[2])
            return 'clients_update', cid
        except Exception:
            return '404', None
    if path.startswith('/clients/') and path.endswith('/delete') and environ['REQUEST_METHOD'] == 'POST':
        try:
            cid = int(path.split('/')[2])
            return 'clients_delete', cid
        except Exception:
            return '404', None
    if path == '/reports':
        return 'reports', None
    return '404', None


def application(environ, start_response):
    init_db()
    r, arg = route(environ)
    if r == 'root':
        return http_redirect(start_response, '/clients')
    if r == 'static':
        return static_app(environ, start_response)
    if r == 'clients_list':
        return clients_list(environ, start_response)
    if r == 'clients_new':
        return client_form(environ, start_response)
    if r == 'clients_create':
        return clients_create(environ, start_response)
    if r == 'clients_edit':
        c = fetch_client_by_id(arg)
        if not c:
            return not_found(start_response)
        return client_form(environ, start_response, c)
    if r == 'clients_update':
        return clients_update(environ, start_response, arg)
    if r == 'clients_delete':
        return clients_delete(environ, start_response, arg)
    if r == 'reports':
        return reports(environ, start_response)
    return not_found(start_response)
