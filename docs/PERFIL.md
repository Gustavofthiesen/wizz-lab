# Perfil do Instagram

Texto e imagens do perfil. As imagens saem de `python tools/gerar_perfil.py`,
em `assets/perfil/`.

## Nome (campo "Nome", 30 caracteres, indexado na busca)

```
Wizz · Valuation e Alocação
```

27 caracteres. Este campo é o que a busca do Instagram lê — o @ pesa menos.
Por isso ele carrega os dois substantivos que descrevem a conta, não um slogan.

## Biografia (150 caracteres)

**Versão principal — 133 caracteres:**

```
Valuation e alocação de longo prazo.
Métricas de portfólio em código aberto.
Uma conta real, medida — inclusive quando o número é ruim.
```

A terceira linha é a que faz o trabalho. Dizer que o resultado é publicado
mesmo quando é ruim só tem valor porque é verificável: o post de abertura abre
com a janela reservada, cujo excesso ajustado tem t = 0,23. Quem for conferir,
confere.

**Alternativa — 146 caracteres, se o foco for o ferramental:**

```
Como se avalia um portfólio, com o código junto.
153 métricas abertas no GitHub.
E o resultado de uma conta real, com as ressalvas.
```

**Alternativa — 118 caracteres, mais curta e mais seca:**

```
Valuation, alocação e medição de carteira.
Ferramental aberto.
Resultado publicado com erro-padrão.
```

O que nenhuma versão faz: promessa de retorno, imperativo ("aprenda",
"descubra"), segunda pessoa, ou os termos proibidos pelo manual de marca
(*trading*, *signals*, *calls*). `brand.checar_titulo()` reprova esses.

## Link

Um link só, para o repositório:

```
github.com/Gustavofthiesen/wizz-lab
```

Se depois houver mais de um destino (repositório, Notion público, lista de
e-mail), vale um agregador — mas enquanto o destino é um, mandar para o
repositório é mais forte que mandar para uma página de links.

## Imagens

| Arquivo | Medida | Onde |
|---|---|---|
| `avatar_marfim.png` | 1080×1080 | foto de perfil, fundo claro |
| `avatar_petroleo.png` | 1080×1080 | foto de perfil, fundo escuro |
| `destaque_metricas.png` | 1080×1920 | capa de destaque |
| `destaque_resultados.png` | 1080×1920 | capa de destaque |
| `destaque_metodo.png` | 1080×1920 | capa de destaque |
| `destaque_codigo.png` | 1080×1920 | capa de destaque |

O avatar é recortado em círculo pelo Instagram e exibido a ~110 px. O gerador
corta o símbolo na caixa de tinta antes de posicionar — o arquivo de origem tem
folga branca e o desenho não está centrado nele, então dimensionar pelo arquivo
entrega um avatar pequeno e levemente torto.

**Entre os dois avatares, o petróleo.** Ele é mais distinguível na linha do
feed, onde o avatar aparece sobre fundo branco e o marfim quase some.

## Uma pendência de marca

O símbolo é um bitmap, e o próprio manual (§5) o classifica como *direção
conceitual*, a ser redesenhada em vetor. Duas consequências práticas:

1. Em tamanhos grandes (capa, impressão) ele vai mostrar artefato de JPEG.
2. As barrinhas do gráfico dentro do símbolo são **violeta** — uma cor que não
   está na paleta e que o manual proíbe explicitamente ("roxo intenso"). Num
   avatar de 110 px não se vê; num card ampliado, vê.

Nada disso bloqueia o lançamento. Mas o redesenho vetorial é a primeira coisa a
encomendar quando houver orçamento.
