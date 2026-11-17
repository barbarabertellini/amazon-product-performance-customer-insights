# Dicionário dos dados reestruturados

Proposta em CSV UTF-8 com BOM, sem índice. Use os tipos abaixo e leia com keep_default_na=False, na_values=["__AUSENTE__"] e float_precision="round_trip". Preços em INR e descontos na escala 0–100.

## ocorrencias_base

Grão: posição no CSV original. Chave: ocorrencia_id.
| Coluna | Tipo | Chave | Nulos | Significado e limite |
|---|---|---|---:|---|
| `ocorrencia_id` | string | PK  | 0 | Chave interna OC- + (source_index + 1), com seis dígitos. Uma ocorrência. |
| `source_index` | Int64 |   | 0 | Posição base zero da linha original; preserva a ordem da fonte. |
| `product_id` | string |  produtos.product_id | 0 | Identificador original de produto; não comprova identidade física de outros IDs. |
| `product_name` | string |   | 0 | Nome literal do produto. |
| `category` | string |   | 0 | Caminho literal da categoria, delimitado por barra vertical. |
| `discounted_price` | string |   | 0 | Preço com desconto literal, em INR, com símbolo/apresentação originais. |
| `actual_price` | string |   | 0 | Preço original literal, em INR. |
| `discount_percentage` | string |   | 0 | Percentual literal, incluindo o símbolo %. |
| `rating` | string |   | 0 | Nota agregada literal do produto; o valor inválido permanece preservado. |
| `rating_count` | string |   | 2 | Contagem agregada literal; não é quantidade de IDs listados. |
| `about_product` | string |   | 0 | Descrição literal integral do produto. |
| `user_id` | string |   | 0 | Em ocorrências, lista literal; em usuários/reviews/ponte, identificador original individualizado. |
| `user_name` | string |   | 0 | Lista literal de nomes, inclusive vírgulas ambíguas; sem correção na fonte. |
| `review_id` | string |   | 0 | Em ocorrências, lista literal; em reviews/ponte, identificador original individualizado. |
| `review_title` | string |   | 0 | Bloco literal integral de títulos da ocorrência; sem atribuição individual. |
| `review_content` | string |   | 0 | Bloco literal integral de conteúdo da ocorrência; sem atribuição individual. |
| `img_link` | string |   | 0 | URL literal de imagem; não comprova identidade. |
| `product_link` | string |   | 0 | URL literal de produto. |
| `grupo_textual_id` | string |   | 0 | TXT- + (mínimo source_index do par exato título/conteúdo + 1), seis dígitos; grupo, não review. |

## categorias

Grão: caminho literal completo. Chave: categoria_id.
| Coluna | Tipo | Chave | Nulos | Significado e limite |
|---|---|---|---:|---|
| `categoria_id` | string | PK  | 0 | Chave CAT + SHA-256 UTF-8 do caminho literal completo. FK no cadastro Produtos. |
| `category_original` | string |   | 0 | Caminho literal da ocorrência de referência; estável por produto nesta fonte. |
| `categoria_nivel_1` | string |   | 0 | Segmento literal 1 do caminho, separação exclusiva por barra vertical; nulo se o nível não existe. |
| `categoria_nivel_2` | string |   | 0 | Segmento literal 2 do caminho, separação exclusiva por barra vertical; nulo se o nível não existe. |
| `categoria_nivel_3` | string |   | 4 | Segmento literal 3 do caminho, separação exclusiva por barra vertical; nulo se o nível não existe. |
| `categoria_nivel_4` | string |   | 37 | Segmento literal 4 do caminho, separação exclusiva por barra vertical; nulo se o nível não existe. |
| `categoria_nivel_5` | string |   | 143 | Segmento literal 5 do caminho, separação exclusiva por barra vertical; nulo se o nível não existe. |
| `categoria_nivel_6` | string |   | 192 | Segmento literal 6 do caminho, separação exclusiva por barra vertical; nulo se o nível não existe. |
| `categoria_nivel_7` | string |   | 204 | Segmento literal 7 do caminho, separação exclusiva por barra vertical; nulo se o nível não existe. |
| `categoria_macro_original` | string |   | 0 | Primeiro segmento literal da hierarquia. |
| `categoria_especifica` | string |   | 0 | Último segmento existente. Pode ser homônimo em caminhos distintos. |
| `profundidade_categoria` | Int64 |   | 0 | Número de segmentos no caminho completo. |
| `categoria_macro_ml` | string |   | 211 | Macro comercial futura. Nula até avaliação. |
| `metodo_macro_ml` | string |   | 211 | Método futuro de macroclassificação. Nulo na proposta. |
| `versao_macro_ml` | string |   | 211 | Versão futura da taxonomia ou modelo. Nula na proposta. |
| `status_macro_ml` | string |   | 0 | PENDENTE enquanto a classificação futura não for avaliada. |

## produtos

Grão: ID de produto. Chave: product_id.
| Coluna | Tipo | Chave | Nulos | Significado e limite |
|---|---|---|---:|---|
| `product_id` | string | PK  | 0 | Identificador original de produto; não comprova identidade física de outros IDs. |
| `product_name` | string |   | 0 | Atributo literal da ocorrência comercial selecionada. |
| `about_product` | string |   | 0 | Atributo literal da ocorrência comercial selecionada. |
| `product_link` | string |   | 0 | Atributo literal da ocorrência comercial selecionada. |
| `img_link` | string |   | 0 | Atributo literal da ocorrência comercial selecionada. |
| `source_index_referencia` | Int64 |   | 0 | Posição base zero da única linha de origem dos atributos selecionados. |
| `actual_price_num` | Float64 |   | 0 | Preço original observado convertido para número, em INR. |
| `discounted_price_num` | Float64 |   | 0 | Preço com desconto observado convertido para número, em INR. |
| `discount_percentage_num` | Float64 |   | 0 | Percentual observado, escala 0–100. |
| `rating_num` | Float64 |   | 1 | Nota agregada observada entre 1 e 5; nula quando inválida. |
| `rating_count_num` | Int64 |   | 2 | Contagem observada inteira não negativa; nula quando ausente/inválida. |
| `rating_analitico_num` | Float64 |   | 0 | Cenário: nota observada ou estimativa 4,1 no único caso elegível; nunca altera rating_num. |
| `rating_estimado` | boolean |   | 0 | True somente quando a nota de cenário é estimada. |
| `metodo_estimativa_rating` | string |   | 1350 | Método e amostra da nota estimada; nulo quando não estimada. |
| `rating_count_analitico_num` | Int64 |   | 0 | Cenário: contagem observada ou mediana 3.049 nos dois casos elegíveis. |
| `rating_count_estimado` | boolean |   | 0 | True somente quando a contagem de cenário é estimada. |
| `metodo_estimativa_rating_count` | string |   | 1349 | Método e amostra da contagem estimada; nulo nos demais casos. |
| `rating_count_situacao` | string |   | 0 | Informado, Não informado ou Formato inválido, conforme o campo bruto/conversão. |
| `quantidade_ocorrencias_origem` | Int64 |   | 0 | Quantidade de linhas originais com o ID do produto. |
| `conflito_preco_original` | boolean |   | 0 | True se o ID tem mais de um valor de actual_price_num entre suas ocorrências, incluindo ausências; não confirma erro. |
| `conflito_preco_desconto` | boolean |   | 0 | True se o ID tem mais de um valor de discounted_price_num entre suas ocorrências, incluindo ausências; não confirma erro. |
| `conflito_percentual` | boolean |   | 0 | True se o ID tem mais de um valor de discount_percentage_num entre suas ocorrências, incluindo ausências; não confirma erro. |
| `conflito_contagem` | boolean |   | 0 | True se o ID tem mais de um valor de rating_count_num entre suas ocorrências, incluindo ausências; não confirma erro. |
| `conflito_descricao` | boolean |   | 0 | True se o ID tem mais de um valor de about_product entre suas ocorrências, incluindo ausências; não confirma erro. |
| `conflito_imagem` | boolean |   | 0 | True se o ID tem mais de um valor de img_link entre suas ocorrências, incluindo ausências; não confirma erro. |
| `criterio_selecao_referencia` | string |   | 0 | Ocorrência única; mesma combinação; combinação mais frequente; ou desempate pela ordem. |
| `ocorrencia_id_referencia` | string |  ocorrencias_base.ocorrencia_id | 0 | Ocorrência real que fornece os atributos do produto. |
| `categoria_id` | string |  categorias.categoria_id | 0 | Chave CAT + SHA-256 UTF-8 do caminho literal completo. FK no cadastro Produtos. |

## usuarios

Grão: ID de usuário. Chave: user_id.
| Coluna | Tipo | Chave | Nulos | Significado e limite |
|---|---|---|---:|---|
| `user_id` | string | PK  | 0 | Em ocorrências, lista literal; em usuários/reviews/ponte, identificador original individualizado. |
| `quantidade_reviews_distintos` | int64 |   | 0 | Número de review_id distintos associados ao usuário na ponte validada. |
| `user_name_recuperado` | string |   | 53 | Único nome não vazio consistente em linhas com quantidades compatíveis; espaços externos removidos somente aqui. |
| `aparece_em_nome_ambiguo` | boolean |   | 0 | ID aparece em pelo menos uma linha com quantidade de nomes incompatível; pode ter nome recuperável em outra linha. |
| `situacao_nome` | string |   | 0 | Associação posicional consistente; sem nome recuperável; ou nomes divergentes em linhas compatíveis. |

## reviews

Grão: ID de review. Chave: review_id.

| Coluna | Tipo | Chave | Nulos | Significado |
|---|---|---|---:|---|
| `review_id` | string | PK | 0 | Em ocorrências, lista literal; em reviews/ponte, identificador original individualizado. |
| `user_id` | string | FK | 0 | Em ocorrências, lista literal; em usuários/reviews/ponte, identificador original individualizado. |
| `quantidade_ocorrencias` | int64 |  | 0 | Número de aparições posicionais do review; não é quantidade de avaliações independentes. |
| `quantidade_produtos_associados` | int64 |  | 0 | Número de product_id distintos em que o review é listado. |
| `review_title` | string |  | 9062 | Trecho literal individual sustentado pela origem indicada. Nulo quando pendente ou conflitante. |
| `ocorrencia_titulo_referencia_id` | string | FK | 9062 | Ocorrência que sustenta o título aceito. FK opcional. |
| `status_recuperacao_titulo` | string |  | 0 | Classificação da evidência do título individual, descrita abaixo. |
| `review_title_candidato` | string |  | 624 | Hipótese plausível de título separada do campo aceito. |
| `quantidade_evidencias_titulo` | Int64 |  | 0 | Número de outras ocorrências com lista e bloco distintos apoiando a melhor hipótese de título. |
| `quantidade_alternativas_titulo` | Int64 |  | 0 | Número de títulos literais distintos entre primeiras hipóteses dos contextos do ID. |
| `review_content` | string |  | 9059 | Trecho literal individual sustentado pela origem indicada. Nulo quando pendente ou conflitante. |
| `ocorrencia_conteudo_referencia_id` | string | FK | 9059 | Ocorrência que sustenta o conteúdo aceito. FK opcional. |
| `status_recuperacao_conteudo` | string |  | 0 | Classificação da evidência do conteúdo individual, descrita abaixo. |
| `review_content_candidato` | string |  | 3647 | Hipótese plausível de conteúdo separada do campo aceito. |
| `quantidade_evidencias_conteudo` | Int64 |  | 0 | Número de outras ocorrências com lista e bloco distintos apoiando a melhor hipótese de conteúdo. |
| `quantidade_alternativas_conteudo` | Int64 |  | 0 | Número de conteúdos literais distintos entre primeiras hipóteses dos contextos do ID. |
| `metodo_recuperacao` | string |  | 9023 | Métodos aceitos para os campos recuperados. Nulo quando ambos estão pendentes. |
| `status_consistencia` | string |  | 0 | Síntese dos status pendentes com prioridade por tipo de evidência. |
| `hash_texto_recuperado` | string |  | 9023 | SHA-256 do JSON UTF-8 [título, conteúdo], com null para campo ausente. |
| `elegivel_ml_textual` | boolean |  | 0 | Ambos os campos confirmados pela fonte ou consistentes por múltiplas evidências. Sem validação humana. |
| `grupo_uso_textual` | string |  | 0 | MAIOR_CONFIANCA, EXPLORATORIO, PENDENTE ou EXCLUIDO_CONFLITO. |
| `divergencia_metodos_titulo` | boolean | | 0 | Primeiras hipóteses de métodos distintos discordam na mesma posição e origem. |
| `ambiguidade_titulo` | boolean | | 0 | Duas alternativas globais próximas diferem no trecho desse campo. |
| `divergencia_entre_ocorrencias_titulo` | boolean | | 0 | Primeiras hipóteses distintas entre origens. Sem confirmação de autoria. |
| `divergencia_metodos_conteudo` | boolean | | 0 | Primeiras hipóteses de métodos distintos discordam na mesma posição e origem. |
| `ambiguidade_conteudo` | boolean | | 0 | Duas alternativas globais próximas diferem no trecho desse campo. |
| `divergencia_entre_ocorrencias_conteudo` | boolean | | 0 | Primeiras hipóteses distintas entre origens. Sem confirmação de autoria. |
| `divergencia_entre_ocorrencias` | boolean | | 0 | Primeiras hipóteses distintas entre origens. Sem confirmação de autoria. |
| `conflito_confirmado` | boolean | | 0 | Blocos unitários incompatíveis em pelo menos um campo. |

Status aceitos mantêm a definição estrutural anterior: bloco unitário, múltiplas evidências ou reconstrução automática. Os status pendentes separam divergência metodológica, ambiguidade, divergência entre ocorrências e conflito confirmado. Consulte o relatório para a regra completa.

## vinculos_reviews

Grão: posição de review na ocorrência. Chave: ocorrencia_id, posicao_na_linha.
| Coluna | Tipo | Chave | Nulos | Significado e limite |
|---|---|---|---:|---|
| `ocorrencia_id` | string | PK ocorrencias_base.ocorrencia_id | 0 | Chave interna OC- + (source_index + 1), com seis dígitos. Uma ocorrência. |
| `source_index` | Int64 |   | 0 | Posição base zero da linha original; preserva a ordem da fonte. |
| `product_id` | string |  produtos.product_id | 0 | Identificador original de produto; não comprova identidade física de outros IDs. |
| `posicao_na_linha` | int64 | PK  | 0 | Posição base um na lista original; compõe a chave da ponte com ocorrencia_id. |
| `review_id` | string |  reviews.review_id | 0 | Em ocorrências, lista literal; em reviews/ponte, identificador original individualizado. |
| `user_id` | string |  usuarios.user_id | 0 | Em ocorrências, lista literal; em usuários/reviews/ponte, identificador original individualizado. |

