# 提交结果对比分析

这个文件记录两次 Kaggle 提交的公榜结果，并分析为什么“清洗 + 特征工程”版本反而不如 baseline。

## 公榜结果

| 提交文件 | Kaggle 公榜分数 | 结论 |
| --- | ---: | --- |
| `01_submission_baseline.csv` | `0.13374` | 当前最好 |
| `02_submission_cleaning_modeling.csv` | `0.14347` | 明显变差 |
| `03_submission_improve_from_baseline.csv` | `0.12629` | 当前最好，明显优于 baseline |
| `04_submission_advanced_linear.csv` | `0.12729` | 不如当前最好 |
| `05_submission_boosting_blend.csv` | `0.12585` | 当前最好 |
| `06_submission_weighted_blend.csv` | `0.12549` | 当前最好 |
| `07_submission_xgboost_tuned_blend.csv` | `0.12516` | 当前最好 |
| `08_submission_second_level_blend.csv` | `0.12518` | 略差于当前最好 |
| `09_submission_xgboost_seed_search.csv` | `0.12485` | 当前最好 |
| `10_submission_xgboost_seed_ensemble.csv` | `0.12490` | 略差于当前最好 |

Kaggle 的分数越低越好，所以 baseline 比清洗建模版更好。

## 本地交叉验证结果

| 文件或流程 | 本地 5 折 CV RMSLE | Kaggle 公榜 |
| --- | ---: | ---: |
| `src/train_baseline.py` | `0.14685` | `0.13374` |
| `notebooks/02_data_cleaning_modeling.ipynb` | 约 `0.14448` | `0.14347` |

本地交叉验证显示清洗建模版略好，但 Kaggle 公榜显示它更差。这说明当前交叉验证没有完全反映测试集分布，或者清洗建模版在部分测试样本上出现了不稳定预测。

## 预测差异观察

对两个提交文件逐行比较后发现：

- 共有 `1459` 条测试集预测。
- baseline 预测范围约为 `46187` 到 `803096`。
- 清洗建模版预测范围约为 `45584` 到 `904532`。
- 两个版本预测差异的中位数只有约 `30`，说明大多数样本差异很小。
- 但部分样本差异非常大，最大相对差异约 `71.76%`。

差异最大的几个样本：

| Id | baseline 预测 | 清洗建模版预测 | 差异 |
| ---: | ---: | ---: | ---: |
| `1975` | `516502.84` | `145868.20` | `-370634.64` |
| `2711` | `241356.40` | `405431.70` | `164075.30` |
| `2574` | `315696.38` | `111614.60` | `-204081.78` |
| `2421` | `131972.27` | `72174.61` | `-59797.66` |
| `2504` | `171083.25` | `118836.14` | `-52247.11` |

这说明问题不一定出在整体方向上，而可能出在少数样本被新特征或清洗逻辑严重拉偏。

## 可能原因

1. 特征工程引入了噪声

   `TotalSF`、`TotalBathrooms`、`HouseAge` 等衍生特征虽然直观，但它们和原始特征高度相关。对于 Ridge / ElasticNet 这类线性模型，重复信息和尺度变化可能改变系数组合，导致少数样本预测偏移。

2. 缺失值语义处理不一定适合所有字段

   把一部分缺失值填成 `None` 是合理的，但如果训练集和测试集在这些字段上的分布不同，模型可能对某些稀有类别过度敏感。

3. 本地验证和 Kaggle 公榜分布不完全一致

   本地交叉验证来自训练集，而 Kaggle 公榜来自测试集的一部分。训练集上的改进不一定能泛化到公榜样本。

4. 少数极端预测拖累分数

   RMSLE 虽然比普通 RMSE 更稳健，但大幅低估或高估仍会明显影响分数。清洗建模版在少数 Id 上出现了很大的预测偏移。

## 下一步策略

当前应把 `09_submission_xgboost_seed_search.csv` 作为保留基线，不要直接用清洗建模版或单纯线性模型替代。

建议下一轮新建一个更稳的实验文件，例如：

`notebooks/03_modeling_improve_from_baseline.ipynb`

实验方向：

- 从 baseline 管道开始，只一次添加一种改动，避免同时改变太多东西。
- 先只处理明确有业务含义的缺失值，不急着加入所有衍生特征。
- 对 `GrLivArea` 的明显异常点做单独实验。
- 对高偏态数值特征做 `log1p`，但保留原始 baseline 作为对照。
- 生成每次实验的提交文件，并记录 Kaggle 公榜分数。
- 不以本地 CV 单独决定模型，必须结合 Kaggle 公榜反馈。

## 后续优化实验 1

已新增：

`notebooks/03_modeling_improve_from_baseline.ipynb`

这个 notebook 从 baseline 出发，比较了四个小步实验：

| 实验 | 说明 | 本地 CV RMSLE |
| --- | --- | ---: |
| `A_baseline` | 原始 baseline | `0.14685` |
| `B_no_outliers` | 只移除明显异常点 | `0.11509` |
| `C_log_skewed` | 只对偏态数值特征做 `log1p` | `0.13079` |
| `D_no_outliers_log_skewed` | 移除异常点 + 偏态数值 `log1p` | `0.11247` |

当前 notebook 内本地验证最好的实验是 `D_no_outliers_log_skewed`，并生成了：

`submissions/03_submission_improve_from_baseline.csv`

注意：这个提交文件的预测最大值约为 `979313`，比 baseline 更激进。它值得提交验证，但最终是否保留，必须以 Kaggle 公榜分数为准。

Kaggle 公榜结果已验证：`03_submission_improve_from_baseline.csv` 得分 `0.12629`，优于 baseline 的 `0.13374`。

## 后续优化实验 2

已新增：

`notebooks/04_modeling_advanced_linear.ipynb`

这个 notebook 继续沿用已验证有效的处理方式：

- 移除明显异常点。
- 对偏态数值特征做 `log1p`。

然后比较 Ridge、Lasso、ElasticNet 和简单融合：

| 方案 | 本地 CV RMSLE |
| --- | ---: |
| `lasso` | `0.10990` |
| `elasticnet` | `0.11001` |
| `blend_ridge_lasso_elasticnet` | `0.11013` |
| `blend_ridge_lasso` | `0.11045` |
| `blend_ridge_elasticnet` | `0.11050` |
| `ridge_robust` | `0.11240` |
| `ridge_standard` | `0.11247` |

当前本地验证最好的模型是 `lasso`，并生成了：

`submissions/04_submission_advanced_linear.csv`

注意：该文件最大预测值约为 `1003536`，比上一轮更激进。建议提交验证，但只有 Kaggle 公榜超过 `0.12629` 时，才把它作为新的最好方案。

## 后续优化实验 3

已新增：

`notebooks/05_modeling_boosting_models.ipynb`

安装 XGBoost、LightGBM、CatBoost 后，本轮继续复用已验证有效的数据处理方式：

- 移除明显异常点。
- 对偏态数值特征做 `log1p`。

然后比较高级树模型和线性模型融合：

| 方案 | 本地 CV RMSLE |
| --- | ---: |
| `blend_lasso_xgboost` | `0.10794` |
| `blend_lasso_catboost` | `0.10867` |
| `lasso` | `0.10990` |
| `blend_all` | `0.11014` |
| `blend_lasso_lightgbm` | `0.11029` |
| `catboost` | `0.11436` |
| `xgboost` | `0.11551` |
| `lightgbm` | `0.12374` |

当前本地验证最好的方案是 `blend_lasso_xgboost`，并生成了：

`submissions/05_submission_boosting_blend.csv`

该文件最大预测值约为 `830047`，比 `04_submission_advanced_linear.csv` 的百万级最大值更稳。建议优先提交这个融合版本验证。

Kaggle 公榜结果已验证：`05_submission_boosting_blend.csv` 得分 `0.12585`，优于 `03_submission_improve_from_baseline.csv` 的 `0.12629`。

## 后续优化实验 4

已新增：

`notebooks/06_modeling_weighted_blend.ipynb`

这个 notebook 不新增特征，只针对当前有效的 Lasso / XGBoost 融合做权重搜索：

| 方案 | Lasso 权重 | ElasticNet 权重 | XGBoost 权重 | OOF RMSLE |
| --- | ---: | ---: | ---: | ---: |
| `lasso_xgboost` | `0.65` | `0.00` | `0.35` | `0.10780` |
| `lasso_elasticnet_xgboost` | `0.60` | `0.05` | `0.35` | `0.10781` |
| `lasso_elasticnet_xgboost` | `0.55` | `0.10` | `0.35` | `0.10781` |
| `lasso_xgboost` | `0.70` | `0.00` | `0.30` | `0.10785` |
| `lasso_xgboost` | `0.60` | `0.00` | `0.40` | `0.10785` |

细搜索后，最佳权重为：

- Lasso: `0.65`
- XGBoost: `0.35`

已生成：

`submissions/06_submission_weighted_blend.csv`

该文件最大预测值约为 `882094`。它比 50/50 融合更偏向 Lasso，理论上更贴近当前最强线性模型，但仍保留 XGBoost 的互补信号。

Kaggle 公榜结果已验证：`06_submission_weighted_blend.csv` 得分 `0.12549`，优于 `05_submission_boosting_blend.csv` 的 `0.12585`。

## 后续优化实验 5

已新增：

`notebooks/07_modeling_xgboost_tuning.ipynb`

这个 notebook 固定当前有效的数据处理和 Lasso 模型，只调 XGBoost 作为辅助模型的参数。调参目标不是让 XGBoost 单模型最强，而是让它与 Lasso 融合后更稳。

| 方案 | XGBoost OOF | Lasso 权重 | XGBoost 权重 | 融合 OOF |
| --- | ---: | ---: | ---: | ---: |
| `depth3_lambda7` | `0.11490` | `0.63` | `0.37` | `0.10759` |
| `depth3_lambda3_sub85` | `0.11546` | `0.64` | `0.36` | `0.10763` |
| `depth3_lambda10` | `0.11517` | `0.64` | `0.36` | `0.10774` |
| `current` | `0.11578` | `0.65` | `0.35` | `0.10780` |
| `depth2_lambda5` | `0.11606` | `0.68` | `0.32` | `0.10837` |

最佳配置：

- `n_estimators=1100`
- `learning_rate=0.025`
- `max_depth=3`
- `subsample=0.80`
- `colsample_bytree=0.70`
- `reg_lambda=7`
- `reg_alpha=0.01`
- 融合权重：`0.63 * Lasso + 0.37 * XGBoost`

已生成：

`submissions/07_submission_xgboost_tuned_blend.csv`

该文件最大预测值约为 `860944`，比 `06_submission_weighted_blend.csv` 的 `882094` 略稳。建议提交验证。

Kaggle 公榜结果已验证：`07_submission_xgboost_tuned_blend.csv` 得分 `0.12516`，优于 `06_submission_weighted_blend.csv` 的 `0.12549`。

## 后续优化实验 6

已新增：

`notebooks/08_modeling_second_level_blend.ipynb`

这个 notebook 不重新训练模型，只对已有强提交做预测层二次融合。当前最好提交是 `07_submission_xgboost_tuned_blend.csv`，因此二次融合以它为主锚点。

候选里最保守的是：

| 候选 | 说明 | 最大预测值 | 相对 tuned 的95%差异 |
| --- | --- | ---: | ---: |
| `log_tuned_90_boosting_10` | 90% tuned + 10% boosting，log 空间 | `857804` | `0.2611%` |
| `log_tuned_85_boosting_15` | 85% tuned + 15% boosting，log 空间 | `856238` | `0.3914%` |
| `log_tuned_80_boosting_20` | 80% tuned + 20% boosting，log 空间 | `854674` | `0.5216%` |

本轮选择：

`log_tuned_85_boosting_15`

已生成：

`submissions/08_submission_second_level_blend.csv`

该文件最大预测值约为 `856238`，比当前最好 `07_submission_xgboost_tuned_blend.csv` 的 `860944` 略低。它是一次很保守的微调，适合提交验证。

Kaggle 公榜结果已验证：`08_submission_second_level_blend.csv` 得分 `0.12518`，略差于 `07_submission_xgboost_tuned_blend.csv` 的 `0.12516`。

结论：二次融合方向没有带来稳定提升。后续不应继续加大 `boosting` 旧版本在二次融合中的权重，当前保留基线仍是 `07_submission_xgboost_tuned_blend.csv`。

## 后续优化实验 7

已新增：

`notebooks/09_modeling_xgboost_seed_search.ipynb`

这个 notebook 不改变当前最佳数据处理方式，也不改变 XGBoost 的主要参数，只搜索 XGBoost 的 `random_state`。由于当前 XGBoost 使用了 `subsample` 和 `colsample_bytree`，不同随机种子会带来轻微不同的树结构。

本轮还做了两个筛选结论：

- CatBoost 原生类别特征实验在当前机器上运行偏慢，筛选阶段超时，暂不作为下一版提交方向。
- 少量强特征如 `TotalSF`、`TotalBath`、`HouseAge` 和质量交互项没有超过当前基础融合，暂不采用。

随机种子搜索结果：

| seed | XGBoost OOF | Lasso 权重 | XGBoost 权重 | 融合 OOF |
| ---: | ---: | ---: | ---: | ---: |
| `23` | `0.11440` | `0.62` | `0.38` | `0.10748` |
| `73` | `0.11422` | `0.61` | `0.39` | `0.10749` |
| `123` | `0.11462` | `0.63` | `0.37` | `0.10758` |
| `42` | `0.11490` | `0.63` | `0.37` | `0.10759` |

当前 OOF 最好的方案是：

- XGBoost `random_state=23`
- 融合权重：`0.62 * Lasso + 0.38 * XGBoost`

已生成：

`submissions/09_submission_xgboost_seed_search.csv`

该文件最大预测值约为 `860198`，与 `07_submission_xgboost_tuned_blend.csv` 的 `860944` 接近。建议提交验证，但只有公榜低于 `0.12516` 时，才替代当前最好方案。

Kaggle 公榜结果已验证：`09_submission_xgboost_seed_search.csv` 得分 `0.12485`，优于 `07_submission_xgboost_tuned_blend.csv` 的 `0.12516`。当前保留基线更新为 `09_submission_xgboost_seed_search.csv`。

## 后续优化实验 8

已新增：

`notebooks/10_modeling_xgboost_seed_ensemble.ipynb`

这个 notebook 继续沿用 `09` 的有效方向，不改变数据处理、不改变 XGBoost 参数，只把多个表现好的 XGBoost 随机种子做平均，再和 Lasso 融合。

扩展 seed 搜索结论：

- `seed=9` 的 OOF 接近 `seed=23`，但单独没有超过 `seed=23`。
- 将 `seed=23`、`seed=73`、`seed=9` 平均后，XGBoost OOF 明显改善。
- 最佳融合权重变为 `0.60 * Lasso + 0.40 * XGBoost(seed平均)`。

验证结果：

| 方案 | OOF RMSLE |
| --- | ---: |
| `lasso` | `0.11014` |
| `xgb_seed_23` | `0.11440` |
| `xgb_seed_73` | `0.11422` |
| `xgb_seed_9` | `0.11413` |
| `xgb_seed_mean` | `0.11379` |
| `0.60_lasso_0.40_xgb_mean` | `0.10742` |

已生成：

`submissions/10_submission_xgboost_seed_ensemble.csv`

该文件最大预测值约为 `854565`，比 `09_submission_xgboost_seed_search.csv` 的 `860198` 更保守。建议提交验证，但只有公榜低于 `0.12485` 时，才替代当前最好方案。

Kaggle 公榜结果已验证：`10_submission_xgboost_seed_ensemble.csv` 得分 `0.12490`，略差于 `09_submission_xgboost_seed_search.csv` 的 `0.12485`。

结论：多 seed 平均虽然本地 OOF 更低，但公榜没有超过单 seed 的 `09`。当前最终最佳提交保持为：

`submissions/09_submission_xgboost_seed_search.csv`

最终公榜分数：

`0.12485`

## 当前结论

本项目当前环境下的最佳结果是 `09_submission_xgboost_seed_search.csv`，Kaggle 公榜分数为 `0.12485`。

最终有效方案：

- 移除训练集中 `GrLivArea > 4000` 且 `SalePrice < 300000` 的明显异常点。
- 对偏态数值特征做 `log1p`。
- 使用 LassoCV 作为稳定线性模型。
- 使用调参后的 XGBoost 作为非线性辅助模型。
- 最终融合：`0.62 * Lasso + 0.38 * XGBoost(seed=23)`。

重要经验：

- 大规模清洗和一次性加入较多特征会导致公榜变差。
- 本地 OOF/CV 有参考价值，但不能完全代替 Kaggle 公榜。
- 目前最可靠的提升来自小步调参、融合权重调整和 XGBoost 随机种子搜索。
- `10` 的多 seed 平均 OOF 更好，但公榜略差，说明继续微调的收益已经很小。

因此，当前停止继续优化，保留 `09_submission_xgboost_seed_search.csv` 作为最终最佳提交。
