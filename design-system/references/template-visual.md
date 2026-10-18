# Template como referência visual

As apresentações do projeto são em HTML autocontido e interativo, por decisão do professor. `Template ONS.pptx` é somente a fonte visual. Preserve o arquivo original.

## Mapeamento do original para HTML

| Slide original | Função | Composição HTML |
|---|---|---|
| 1 | Capa fotográfica vermelha com Pecege e ONS | `capa sem-numero`, com imagens extraídas e título/professor |
| 2 | Aviso legal, prédio e símbolo Pecege | `legal sem-numero` |
| 3 | Placeholder vazio | Não precisa ser reproduzido |
| 4 | Conteúdo claro, rodapé e numeração | Base padrão de `.slide` |
| 5 | Conteúdo com ondas claras | Variante `.ondas`, com inversão vertical do ativo original |
| 6 | Agradecimento | `encerramento sem-numero`, antes das referências |
| 7 | Tela institucional com marcas | Opcional; não é slide de conteúdo |

O mestre do original usa Arial, títulos `#F20C3A`, corpo `#60697C`, fundo `#F9F9F9` e rodapé institucional pequeno. As fontes e cores do tema Office embutido não representam a composição efetivamente usada. A grade HTML normaliza o 16:9 para 1600×900 e amplia o corpo para leitura em aula remota.

Os ativos são extraídos por `tools/extrair-template.py`; sua origem e o hash do template ficam em `assets/proveniencia.json`. A adaptação permite ampliar a caixa do título da capa e compor conteúdo livremente, mantendo marcas, paleta e rodapé.
