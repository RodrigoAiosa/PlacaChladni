# Placa de Chladni

Explorador interativo das figuras de Chladni, em **Python (numpy) + Vercel**.
A areia se acumula nas linhas nodais (w = 0) de cada modo de vibração da placa.

## Variações
| Placa | Modo | Fórmula |
|---|---|---|
| Quadrada | (m, n), simétrico e antissimétrico | `cos(nπx)cos(mπy) ± cos(mπx)cos(nπy)` |
| Retangular | (m, n) + proporção livre | `cos(nπx)cos(mπy)`, f² ∝ (n/a)² + m² |
| Circular | (k anéis, n diâmetros) | `J_n(z_{n,k} r) cos(nθ)` |
| Anel | (k, n) + raio interno | combinação `J_n`/`Y_n` com nós nos dois raios |
| Superposição | (m, n) + mistura | `cos·cos + mix·cos·cos` |

A galeria gera **todos** os modos até a ordem escolhida, ordenados por frequência.
Visualizações: areia animada, linhas nodais, mapa de deslocamento, placa vibrando e som.

> Modelo didático: os modos quadrado/retangular usam a aproximação clássica de cossenos
> (bordas livres idealizadas); circular e anel são membranas presas.

## Estrutura
```
api/_chladni.py   núcleo matemático (numpy)
api/pattern.py    GET /api/pattern?plate=&m=&n=&sign=&aspect=&mix=&inner=&res=
api/gallery.py    GET /api/gallery?plate=&kmax=&res=
api/plates.py     GET /api/plates
public/           front-end estático (HTML/CSS/JS canvas)
dev.py            servidor local
```

## Rodar local
```bash
pip install -r requirements.txt pytest
python dev.py          # http://localhost:3000
pytest
```
ou `vercel dev`.

## Deploy
Importe o repositório em [vercel.com/new](https://vercel.com/new) (sem configuração extra) ou `vercel --prod`.
