# Evaluation Prompt

Source theory file:

`src/example/A_unified_theory_of_tobin's_q,_corporate_investment,_financing,_and_risk_management.md`

## Exact User Prompt

```text
基于src/example/A_unified_theory_of_tobin's_q,_corporate_investment,_financing,_and_risk_management.md，完成文章中Case II: Refinancing的代码以及画图，将结果生成在skills/finhjb-model-coder/tests 文件夹中的 BCWrefinancing.py 中
```

## Interaction Requirement Added During Evaluation

```text
要测试这个 SKILL 的能力，就代表你需要基于我给你的文章，和我进行交互，确认一系列的模型内容，而不是直接生成代码
```

## Locked Evaluation Intent

- evaluate `finhjb-model-coder` as an interactive assistant
- use the paper as the sole theory source
- target BCW `Case II: Refinancing`
- cover the full Figure 3 comparison with `phi = 1%` and `phi = 0`
