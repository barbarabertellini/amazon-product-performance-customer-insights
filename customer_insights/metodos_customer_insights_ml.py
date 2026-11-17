"""Métodos auditáveis da etapa textual. Importar não grava nem treina nada."""
from pathlib import Path
import re, json, hashlib, unicodedata
import numpy as np
import pandas as pd

VERSAO = 'ci_ml_v1_20261110'
REGRAS = {
    'Charging/charger (candidato)': r'\b(?:charging|charger|chargers)\b',
    'Bateria': r'\b(?:battery|batteries)\b',
    'Som e áudio': r'\b(?:sound|audio|speaker|speakers)\b',
    'Referência a value for money': r'\bvalue for money\b',
    'Referência a facilidade de uso/instalação/limpeza': r'\beasy to (?:use|install|clean)\b',
}

def localizar_raiz():
    return next(c for p in [Path.cwd(), *Path.cwd().parents]
                for c in [p, p/'amazon_sales_analise'] if (c/'dados_tratados/produtos.csv').is_file())

def ler_tabelas(raiz):
    """Carrega as seis entidades e deriva os campos usados pela análise existente."""
    import sys
    if str(raiz) not in sys.path:
        sys.path.insert(0,str(raiz))
    from leitura_dados import ler_canonicas, projetar
    return projetar(ler_canonicas(raiz))

def validar_fontes(t,raiz):
    p,o,u,r,v=[t[k] for k in ['produtos','ocorrencias_catalogo','usuarios','avaliacoes_identificadas','vinculos_avaliacoes']]
    checks=[]
    def check(nome,cond):
        if not bool(cond): raise ValueError(nome)
        checks.append({'Teste':nome,'Aprovado':True})
    for nome,d,ch in [('produtos',p,['product_id']),('ocorrências',o,['ocorrencia_id']),('usuários',u,['user_id']),('reviews',r,['review_id']),('ponte',v,['ocorrencia_id','posicao_na_linha'])]:
        check(nome+': chave completa única',d[ch].notna().all().all() and not d.duplicated(ch).any())
    for campo,dim in [('product_id',p),('ocorrencia_id',o),('review_id',r),('user_id',u)]:
        check('FK ponte '+campo,v[campo].isin(dim[campo]).all())
    check('Cobertura de produtos',set(p.product_id)==set(o.product_id))
    ctx=v.merge(o[['ocorrencia_id','product_id','source_index','grupo_textual_id']],on='ocorrencia_id',suffixes=('','_origem'),validate='many_to_one')
    check('Produto e origem da ponte',ctx.product_id.eq(ctx.product_id_origem).all() and ctx.source_index.eq(ctx.source_index_origem).all())
    ctx=ctx.merge(r[['review_id','user_id']],on='review_id',suffixes=('','_review'),validate='many_to_one')
    check('Usuário contextual consistente',ctx.user_id.eq(ctx.user_id_review).all() and r.user_id.isin(u.user_id).all())
    check('Posições consecutivas',v.groupby('ocorrencia_id').posicao_na_linha.apply(lambda s:sorted(s)==list(range(1,len(s)+1))).all())
    ordenada=v.sort_values(['ocorrencia_id','posicao_na_linha'])
    for campo in ['review_id','user_id']:
        reconstruido=ordenada.groupby('ocorrencia_id')[campo].agg(list)
        esperado=o.set_index('ocorrencia_id')[campo].map(lambda s:[item.strip() for item in s.split(',')])
        check('Listas posicionais reconstruídas '+campo,reconstruido.equals(esperado.reindex(reconstruido.index)))
    check('Junção preserva 11.503 posições',len(ctx)==len(v)==11503)
    par=o[['review_title','review_content','grupo_textual_id']].drop_duplicates()
    check('Par exato bijetivo com grupo',par.grupo_textual_id.is_unique and not par.duplicated(['review_title','review_content']).any())
    bruto=pd.read_csv(raiz/'amazon.csv',dtype='string',keep_default_na=False)
    for c in ['review_title','review_content']:
        check('Original integral '+c,o.sort_values('source_index')[c].reset_index(drop=True).equals(bruto[c]))
    ref=p.merge(o,on='product_id',suffixes=('_p','_o'),validate='one_to_many')
    ref=ref.loc[ref.source_index_referencia.eq(ref.source_index)]
    check('Uma referência real por produto',len(ref)==len(p) and ref.product_id.is_unique)
    for c in ['rating_num','rating_count_num','actual_price_num','discounted_price_num','discount_percentage_num']:
        check('Medida da referência '+c,((ref[c+'_p']==ref[c+'_o']) | (ref[c+'_p'].isna() & ref[c+'_o'].isna())).fillna(False).all())
    for k in range(1,8):
        check('Hierarquia '+str(k),p[f'categoria_nivel_{k}'].equals(p.category_original.str.split('|',regex=False).str[k-1].astype('string')))
    from leitura_dados import projetar_blocos
    proj=projetar_blocos(o)
    check('Projeção de blocos 1:1',len(proj)==len(o) and proj.ocorrencia_id.is_unique)
    check('199 reviews multicontexto',ctx.groupby('review_id').grupo_textual_id.nunique().gt(1).sum()==199)
    return pd.DataFrame(checks),ctx,proj

def perfis_oficiais(p,grupos=('categoria_nivel_1',)):
    d=p.copy();permitido=d.categoria_nivel_1.isin(['Electronics','Computers&Accessories','Home&Kitchen'])
    g=d.groupby(list(grupos),dropna=False)
    d['limite_nota']=g.rating_num.transform('median');d['limite_contagem']=g.rating_count_num.transform('median');d['n_grupo']=g.product_id.transform('size')
    presentes=d[['rating_num','rating_count_num']].notna().all(axis=1)
    d['perfil_completo']='Empate';alta=d.rating_num.gt(d.limite_nota);baixa=d.rating_num.lt(d.limite_nota);cont=d.rating_count_num.ge(d.limite_contagem)
    for cond,nome in [(baixa & cont,'A'),(alta & cont,'B'),(alta & ~cont,'Alta/baixa'),(baixa & ~cont,'Baixa/baixa')]:d.loc[cond.fillna(False),'perfil_completo']=nome
    d.loc[~presentes,'perfil_completo']='Ausência';d.loc[~permitido,'perfil_completo']='Fora do recorte'
    return d

def preparar_corpus(t):
    o=t['ocorrencias_catalogo'];p=perfis_oficiais(t['produtos'])
    n2=perfis_oficiais(t['produtos'],('categoria_nivel_1','categoria_nivel_2'))
    p['perfil_n2']=n2.perfil_completo;p['n_n2']=n2.n_grupo
    p['perfil_persistente_n2']=p.perfil_completo.eq(p.perfil_n2)
    tres=p.perfil_completo.ne('Fora do recorte')
    assert int((tres & ~p.perfil_persistente_n2).sum())==229
    assert (int((tres & p.n_n2.ge(30)).sum()),int((tres & p.n_n2.ge(30) & ~p.perfil_persistente_n2).sum()))==(1193,167)
    assert p.perfil_completo.value_counts().reindex(['A','B','Alta/baixa','Baixa/baixa','Empate','Ausência','Fora do recorte']).tolist()==[212,299,241,330,228,3,38]
    corpus=o.sort_values('source_index').drop_duplicates('grupo_textual_id')[['grupo_textual_id','review_title','review_content']].reset_index(drop=True)
    for c in ['review_title','review_content']:corpus[c+'_normalizado']=corpus[c].str.normalize('NFC').str.replace(r'[^\S\r\n]+',' ',regex=True)
    corpus['texto_busca']=(corpus.review_title_normalizado+' '+corpus.review_content_normalizado).str.replace(r'https?://[^\s,<>]+',' ',regex=True).str.lower()
    corpus['caracteres']=corpus.review_content.str.len()
    corpus['tem_url']=corpus.review_content.str.contains(r'https?://')
    corpus['sinal_devanagari']=corpus.texto_busca.str.contains(r'[\u0900-\u097F]')
    corpus['sinal_tamil']=corpus.texto_busca.str.contains(r'[\u0B80-\u0BFF]')
    corpus['sinal_outros_sistemas_indicos']=corpus.texto_busca.str.contains(r'[\u0980-\u0B7F\u0C00-\u0D7F]')
    corpus['sinal_latino']=corpus.texto_busca.str.contains(r'[a-zA-Z]')
    corpus['triagem_escrita']=np.where(corpus[['sinal_devanagari','sinal_tamil','sinal_outros_sistemas_indicos']].any(axis=1),'Escrita índica presente; idioma não confirmado','Sem escrita índica detectada; idioma não confirmado')
    corpus['elegivel_busca']=corpus.review_content.notna() & corpus.review_content.str.strip().ne('')
    corpus['sha256_texto']=corpus.apply(lambda row:hashlib.sha256(json.dumps([row.review_title,row.review_content],ensure_ascii=False).encode()).hexdigest(),axis=1)
    for nome,regra in REGRAS.items():corpus[nome]=corpus.texto_busca.str.contains(regra)
    links=o[['ocorrencia_id','source_index','product_id','grupo_textual_id']].copy()
    pg=links[['product_id','grupo_textual_id']].drop_duplicates()
    ctx=links.merge(p,on='product_id',validate='many_to_one')
    cobertura=ctx.groupby('perfil_completo').agg(Produtos=('product_id','nunique'),Grupos=('grupo_textual_id','nunique'),Ocorrências=('ocorrencia_id','size'))
    return corpus,links,pg,p,cobertura

def agregar_produtos(p,pg,corpus):
    campos=list(REGRAS)+['elegivel_busca']
    m=pg.merge(corpus[['grupo_textual_id']+campos],on='grupo_textual_id',validate='many_to_one')
    flags=m.groupby('product_id')[campos].any()
    out=p.merge(flags,on='product_id',validate='one_to_one')
    out['grupos_textuais']=out.product_id.map(pg.groupby('product_id').size()).astype('Int64')
    assert len(out)==1351 and out.product_id.is_unique
    return out

def contrastes_locais(visao,dimensao='category_original',somente_persistentes=False):
    d=visao.loc[visao.perfil_completo.isin(['A','B','Alta/baixa'])]
    if somente_persistentes:d=d.loc[d.perfil_persistente_n2 & d.n_n2.ge(30)]
    rows=[]
    for grupo,s in d.groupby(dimensao):
        for perfil in ['A','Alta/baixa']:
            a=s.loc[s.perfil_completo.eq(perfil)];b=s.loc[s.perfil_completo.eq('B')]
            if min(len(a),len(b))<5:continue
            for tema in list(REGRAS)[1:]:
                rows.append({'Grupo':grupo,'Perfil':perfil,'Menção':tema,'n perfil':len(a),'n B':len(b),'Com menção perfil':int(a[tema].sum()),'Com menção B':int(b[tema].sum()),'% perfil':100*a[tema].mean(),'% B':100*b[tema].mean(),'Diferença pp':100*(a[tema].mean()-b[tema].mean())})
    return pd.DataFrame(rows)

def componentes(corpus,links,ctx,pares_similares=None):
    parent={}
    def find(x):
        parent.setdefault(x,x)
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b:parent[b]=a
    for p,g in links[['product_id','grupo_textual_id']].drop_duplicates().itertuples(index=False,name=None):union('P:'+p,'T:'+g)
    for r,g in ctx[['review_id','grupo_textual_id']].drop_duplicates().itertuples(index=False,name=None):union('R:'+r,'T:'+g)
    if pares_similares is not None:
        for a,b in pares_similares[['grupo_a','grupo_b']].itertuples(index=False,name=None):union('T:'+a,'T:'+b)
    ids=corpus.grupo_textual_id;roots=[find('T:'+g) for g in ids]
    nomes={r:f'C{i+1:04d}' for i,r in enumerate(dict.fromkeys(roots))}
    return pd.DataFrame({'grupo_textual_id':ids,'componente': [nomes[r] for r in roots]})

def similaridade_proxima(corpus):
    """Triagem lexical de quase duplicação; não é prova de equivalência semântica."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    vec=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),min_df=2,max_features=30000,sublinear_tf=True)
    x=vec.fit_transform(corpus.texto_busca)
    sim=cosine_similarity(x);np.fill_diagonal(sim,0)
    ii,jj=np.where(np.triu(sim>=0.80,1))
    pairs=pd.DataFrame({'grupo_a':corpus.grupo_textual_id.iloc[ii].to_numpy(),'grupo_b':corpus.grupo_textual_id.iloc[jj].to_numpy(),'cosseno':sim[ii,jj]})
    return pairs.sort_values('cosseno',ascending=False).reset_index(drop=True)

def casos_oraculo(visao):
    masks={'Base':pd.Series(True,index=visao.index),'Electronics':visao.categoria_nivel_1.eq('Electronics'),'Electronics + Home':visao.categoria_nivel_1.isin(['Electronics','Home&Kitchen']),'Electronics / Headphones':visao.categoria_nivel_1.eq('Electronics') & visao.categoria_nivel_2.eq('Headphones,Earbuds&Accessories'),'A':visao.perfil_completo.eq('A'),'Alta/baixa':visao.perfil_completo.eq('Alta/baixa'),'Electronics / A / preço ≤ 899':visao.categoria_nivel_1.eq('Electronics') & visao.perfil_completo.eq('A') & visao.discounted_price_num.le(899),'OfficeProducts':visao.categoria_nivel_1.eq('OfficeProducts'),'Vazio':visao.discounted_price_num.lt(0)}
    rows=[]
    for nome,mask in masks.items():
        d=visao.loc[mask];n=int(d.elegivel_busca.sum())
        for tema in list(REGRAS)[1:]:rows.append({'Caso':nome,'Menção':tema,'Produtos':len(d),'Denominador elegível':n,'Numerador':int(d[tema].sum()),'Percentual':100*d[tema].sum()/n if n else np.nan})
    return pd.DataFrame(rows)

def salvar_csv(d,pasta,nome):
    """Saídas só em experimento provisório ou staging, nunca dados_tratados/BI."""
    pasta=Path(pasta).resolve()
    if not any(x.startswith('EXPERIMENTO_PROVISORIO') or x=='trabalho' for x in pasta.parts):raise ValueError('Destino não experimental')
    pasta.mkdir(parents=True,exist_ok=True)
    d.to_csv(pasta/nome,index=False,encoding='utf-8-sig',na_rep='__AUSENTE__')
    tipos={c:('string' if str(t)=='object' else str(t)) for c,t in d.dtypes.items()}
    relido=pd.read_csv(pasta/nome,dtype=tipos,keep_default_na=False,na_values=['__AUSENTE__'],encoding='utf-8-sig',float_precision='round_trip')
    pd.testing.assert_frame_equal(d.astype(tipos).reset_index(drop=True),relido,check_exact=True,check_names=False)

def testes_negativos(t,raiz):
    results=[]
    for nome in ['Chave duplicada','FK órfã','Texto original alterado']:
        copia={k:v.copy(deep=True) for k,v in t.items()}
        if nome=='Chave duplicada':copia['produtos']=pd.concat([copia['produtos'],copia['produtos'].iloc[:1]],ignore_index=True)
        elif nome=='FK órfã':copia['vinculos_avaliacoes'].loc[0,'product_id']='INEXISTENTE'
        else:copia['ocorrencias_catalogo'].loc[0,'review_content']='ALTERADO'
        try:validar_fontes(copia,raiz)
        except (ValueError,AssertionError):results.append({'Teste negativo':nome,'Detectado':True})
        else:raise AssertionError('Falha não detectada: '+nome)
    return pd.DataFrame(results)

def experimentar_temas(corpus,comp):
    """NMF transdutivo; estabilidade não equivale a validade semântica ou previsão."""
    from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
    from sklearn.decomposition import NMF
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
    from scipy.optimize import linear_sum_assignment
    from threadpoolctl import threadpool_limits
    import warnings
    stop=sorted(set(ENGLISH_STOP_WORDS)-{'no','not','nor','never'})
    config=dict(ngram_range=(1,2),min_df=3,max_df=.85,max_features=10000,sublinear_tf=True,stop_words=stop,token_pattern=r'(?u)\b[^\W\d_][^\W\d_]+\b')
    vector=TfidfVectorizer(**config);x=vector.fit_transform(corpus.texto_busca)
    terms=vector.get_feature_names_out()
    metrics=[];models={};warns=[]
    with threadpool_limits(limits=1):
        for k in [6,10,14]:
            for seed in [42,7,99]:
                model=NMF(n_components=k,init='nndsvdar',random_state=seed,max_iter=1000,tol=1e-4)
                with warnings.catch_warnings(record=True) as ww:
                    w=model.fit_transform(x)
                warns.extend([str(v.message) for v in ww])
                h=model.components_;scale=np.linalg.norm(h,axis=1);scores=w*scale
                labels=scores.argmax(axis=1);counts=np.bincount(labels,minlength=k)
                tops=np.argsort(h,axis=1)[:,-10:]
                sim=cosine_similarity(h);np.fill_diagonal(sim,0)
                metrics.append({'k':k,'semente':seed,'erro_reconstrucao':model.reconstruction_err_,'iteracoes':model.n_iter_,'menor_tema':int(counts.min()),'maior_tema':int(counts.max()),'diversidade_top10':len(set(tops.ravel()))/(k*10),'maior_cosseno_entre_temas':float(sim.max())})
                models[k,seed]=(model,w,scores)
        main,w,scores=models[10,42]
        stability=[]
        for seed in [7,99]:
            other,_,s=models[10,seed];sim=cosine_similarity(main.components_,other.components_);ii,jj=linear_sum_assignment(-sim)
            stability.append({'Perturbação':'Semente; mesmo corpus/vocabulário','semente':seed,'grupos_ajuste':len(corpus),'cosseno_temas_alinhados':sim[ii,jj].mean(),'ARI_atribuicao_global':adjusted_rand_score(scores.argmax(axis=1),s.argmax(axis=1))})
        # Subamostras por componente ampliado; TF-IDF é reajustado só na subamostra.
        components=comp.set_index('grupo_textual_id').loc[corpus.grupo_textual_id,'componente'].to_numpy()
        unique=np.unique(components)
        for seed in [42,7,99]:
            rng=np.random.default_rng(seed);chosen=rng.choice(unique,size=int(.8*len(unique)),replace=False);mask=np.isin(components,chosen)
            vv=TfidfVectorizer(**config);xx=vv.fit_transform(corpus.loc[mask,'texto_busca'])
            mm=NMF(n_components=10,init='nndsvdar',random_state=seed,max_iter=1000,tol=1e-4)
            with warnings.catch_warnings(record=True) as ww:mm.fit(xx)
            warns.extend([str(v.message) for v in ww])
            # Comparar os vetores de tema sobre interseção explícita de vocabulários.
            common,ia,ib=np.intersect1d(terms,vv.get_feature_names_out(),return_indices=True)
            sim=cosine_similarity(main.components_[:,ia],mm.components_[:,ib]);ii,jj=linear_sum_assignment(-sim)
            s=mm.transform(vv.transform(corpus.texto_busca))*np.linalg.norm(mm.components_,axis=1)
            stability.append({'Perturbação':'80% componentes; TF-IDF reajustado','semente':seed,'grupos_ajuste':int(mask.sum()),'cosseno_temas_alinhados':sim[ii,jj].mean(),'ARI_atribuicao_global':adjusted_rand_score(scores.argmax(axis=1),s.argmax(axis=1))})
        # Sensibilidade a termos avaliativos genéricos, não correção de polaridade.
        cfg=config|{'stop_words':sorted(set(stop)|{'good','nice','product','products','quality','great','amazon'})}
        vg=TfidfVectorizer(**cfg);xg=vg.fit_transform(corpus.texto_busca)
        mg=NMF(n_components=10,init='nndsvdar',random_state=42,max_iter=1000,tol=1e-4)
        with warnings.catch_warnings(record=True) as ww:wg=mg.fit_transform(xg)
        warns.extend([str(v.message) for v in ww])
        sg=wg*np.linalg.norm(mg.components_,axis=1)
        common,ia,ib=np.intersect1d(terms,vg.get_feature_names_out(),return_indices=True)
        sim=cosine_similarity(main.components_[:,ia],mg.components_[:,ib]);ii,jj=linear_sum_assignment(-sim)
        stability.append({'Perturbação':'Sem sete termos genéricos','semente':42,'grupos_ajuste':len(corpus),'cosseno_temas_alinhados':sim[ii,jj].mean(),'ARI_atribuicao_global':adjusted_rand_score(scores.argmax(axis=1),sg.argmax(axis=1))})
    if warns:raise RuntimeError('Warnings de ajuste a investigar: '+repr(warns))
    denom=scores.sum(axis=1);shares=np.divide(scores,denom[:,None],out=np.zeros_like(scores),where=denom[:,None]>0)
    order=np.argsort(shares,axis=1);top=shares.max(axis=1);margin=top-shares[np.arange(len(shares)),order[:,-2]]
    eligible=np.asarray(x.getnnz(axis=1)).ravel()>0
    assigned=np.where(~eligible,'Sem vocabulário',np.where((top<.35)|(margin<.10),'Ambíguo',np.array([f'T{v+1:02}' for v in shares.argmax(axis=1)])))
    result=corpus[['grupo_textual_id']].copy();result['tema_dominante']=[f'T{i+1:02}' for i in shares.argmax(axis=1)]
    result['situacao']=assigned;result['peso_relativo_max']=top;result['margem_top2']=margin;result['termos_representados']=np.asarray(x.getnnz(axis=1)).ravel();result['maturidade']='EXPLORATORIO_NAO_VALIDADO';result['versao']=VERSAO
    topics=[];examples=[]
    for j in range(10):
        ids=np.flatnonzero(shares.argmax(axis=1)==j);rank=ids[np.argsort(-shares[ids,j])]
        words=terms[np.argsort(main.components_[j])[-12:][::-1]]
        topics.append({'Tema':f'T{j+1:02}','Termos principais':', '.join(words),'Grupos dominantes':len(ids),'Grupos sem abstenção':int((assigned==f'T{j+1:02}').sum())})
        chosen=list(rank[:2])
        if len(rank):chosen += [rank[len(rank)//2],rank[-1]]
        for position,i in enumerate(dict.fromkeys(chosen)):
            examples.append({'Tema':f'T{j+1:02}','Critério':['Maior peso','Segundo peso','Central','Menor peso'][position],'grupo_textual_id':corpus.iloc[i].grupo_textual_id,'Peso relativo':shares[i,j],'Texto integral':corpus.iloc[i].review_title+'\n'+corpus.iloc[i].review_content})
    weights=pd.DataFrame(shares,columns=[f'T{j+1:02}' for j in range(10)]);weights.insert(0,'grupo_textual_id',corpus.grupo_textual_id)
    thresholds=pd.DataFrame([{'peso_minimo':q,'margem_minima':m,'grupos_sem_abstencao':int((eligible & (top>=q)&(margin>=m)).sum())} for q,m in [(.25,.05),(.35,.10),(.45,.15)]])
    params={'versao':VERSAO,'metodo':'TF-IDF + NMF','k_principal':10,'motivo_k':'Resolução exploratória intermediária pré-especificada; não ótimo validado','sementes':[42,7,99],'k_comparados':[6,10,14],'max_iter':1000,'tol':1e-4,'tfidf':{**config,'token_pattern':config['token_pattern']},'maturidade':'exploratório','rotulos_humanos':False,'limiares_heuristicos':{'peso':.35,'margem':.10},'numero_ajustes_nmf':13}
    return {'metricas':pd.DataFrame(metrics),'estabilidade':pd.DataFrame(stability),'temas':pd.DataFrame(topics),'atribuicoes':result,'pesos':weights,'exemplos':pd.DataFrame(examples),'limiares':thresholds,'parametros':params,'vectorizer':vector,'modelo':main,'x':x}

def piloto_anotacao(corpus,links,p,atribuicoes,comp):
    """Seleção intencional estratificada, sem preencher rótulos humanos."""
    frame=links[['product_id','grupo_textual_id']].drop_duplicates().merge(p[['product_id','categoria_nivel_1','perfil_completo']],on='product_id',validate='many_to_one').merge(comp,on='grupo_textual_id',validate='many_to_one')
    escolhidos=[];usados=set()
    for (cat,perfil),d in frame.loc[frame.perfil_completo.isin(['A','B','Alta/baixa'])].groupby(['categoria_nivel_1','perfil_completo']):
        rng=np.random.default_rng(42);ids=rng.permutation(d.grupo_textual_id.unique())
        count=0
        for gid in ids:
            co=comp.set_index('grupo_textual_id').at[gid,'componente']
            if co in usados:continue
            escolhidos.append(gid);usados.add(co);count+=1
            if count==5:break
    for tema,d in atribuicoes.groupby('tema_dominante'):
        for gid in d.sort_values('peso_relativo_max',ascending=False).grupo_textual_id:
            co=comp.set_index('grupo_textual_id').at[gid,'componente']
            if co not in usados:escolhidos.append(gid);usados.add(co);break
    for gid in corpus.loc[corpus.sinal_devanagari | corpus.sinal_tamil,'grupo_textual_id'].head(5):
        if gid not in escolhidos:escolhidos.append(gid)
    pilot=corpus.loc[corpus.grupo_textual_id.isin(escolhidos),['grupo_textual_id','review_title','review_content']].copy()
    for col in ['anotador_1','anotador_2','idioma_confirmado','aspectos','polaridades_por_aspecto','objeto_da_mencao','trecho_evidencia','discordancia','adjudicacao']:pilot[col]=pd.NA
    pilot['status']='PENDENTE_ANOTACAO_HUMANA'
    return pilot
