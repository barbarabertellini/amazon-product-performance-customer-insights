"""Leitura do modelo canônico e projeções em memória para análises existentes."""
import json
from pathlib import Path
import pandas as pd

def ler_canonicas(raiz):
    raiz = Path(raiz)
    contrato = json.loads((raiz/'documentacao/schema_dados.json').read_text(encoding='utf-8'))
    tabelas = {}
    for nome, spec in contrato['entidades'].items():
        arquivo = raiz/'dados_tratados'/f'{nome}.csv'
        tabela = pd.read_csv(arquivo, dtype=spec['tipos'], encoding='utf-8-sig',
                             keep_default_na=False, na_values=['__AUSENTE__'], float_precision='round_trip')
        if set(tabela.columns) != set(spec['tipos']):
            raise ValueError(f'Esquema incompatível: {arquivo}')
        tabelas[nome] = tabela
    return tabelas

def projetar(t):
    cat = t['categorias']
    niveis = [f'categoria_nivel_{i}' for i in range(1,8)]
    p = t['produtos'].merge(cat[['categoria_id','category_original',*niveis,
        'categoria_macro_original','categoria_especifica']],on='categoria_id',how='left',validate='many_to_one')
    assert p.category_original.notna().all()
    p = p.rename(columns={'about_product':'about_product_referencia','img_link':'img_link_referencia',
        'product_link':'product_link_referencia','quantidade_ocorrencias_origem':'quantidade_observacoes',
        'categoria_macro_original':'categoria_principal','categoria_especifica':'categoria_terminal'})
    o = t['ocorrencias_base'].copy()
    for campo in ['actual_price','discounted_price','discount_percentage','rating','rating_count']:
        limpo = o[campo].str.replace(r'[₹,%]','',regex=True)
        valor = pd.to_numeric(limpo,errors='coerce')
        if campo == 'rating':
            valor = valor.where(valor.between(1,5))
        if campo == 'rating_count':
            valor = valor.where(valor.ge(0) & valor.mod(1).eq(0))
        o[campo+'_num'] = valor.astype('Int64' if campo=='rating_count' else 'Float64')
    o['conteudo_reutilizado'] = o.grupo_textual_id.duplicated(keep=False).astype('boolean')
    return {**t,'produtos':p,'ocorrencias_catalogo':o,
            'avaliacoes_identificadas':t['reviews'],'vinculos_avaliacoes':t['vinculos_reviews']}

def projetar_blocos(o):
    return o[['ocorrencia_id','source_index','product_id','review_title','review_content',
              'grupo_textual_id','conteudo_reutilizado']].rename(columns={
        'review_title':'review_title_original','review_content':'review_content_original'})
