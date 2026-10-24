# Omics Analysis Methods Reference

## 代谢组学分析流程

### 非靶向代谢组学
1. 数据导入（mzML/mzXML 格式）
2. 峰提取与对齐（XCMS / MZmine / PyOpenMS）
3. 缺失值过滤（80% 规则：保留至少在一组中 80% 样本有值的特征）
4. 缺失值插补（最小值的 1/5 或 KNN 插补）
5. 归一化（总离子流/中位数/PQN/内标）
6. 质控（QC-RSD < 30% 过滤）
7. 数据转换（log2 + Pareto scaling）
8. 多变量分析：PCA（无监督）→ PLS-DA / OPLS-DA（有监督）
9. 模型验证：置换检验（≥1000 次，p 接近判断阈值时 10 000 次，与 yaml `resampling` / `omics.dimensionality_reduction` 一致；写明随机种子）、CV-ANOVA
10. VIP 值 > 1 + 单变量 p < 0.05（FDR 校正）筛选差异代谢物
11. 代谢物鉴定（HMDB / METLIN / MassBank）
12. 通路分析（MetaboAnalyst / KEGG）
13. 富集分析（MSEA）

### 靶向代谢组学
1. 标准曲线验证（线性范围、R² > 0.99）
2. 质控样本检查（QC 偏差 < 15%）
3. 低于 LOD 的值处理（LOD/2 或删除）
4. 直接进入统计分析（无需峰提取步骤）

### 代谢组学统计注意事项
- PLS-DA 必须做置换检验和交叉验证，否则结果不可信
- VIP + p-value 双筛选是标准做法
- OPLS-DA 的 R²Y 和 Q²Y 都应报告
- 通路分析应报告 impact 值和 FDR 校正后的 p 值

## 蛋白质组学分析流程

1. 原始数据处理（MaxQuant / Proteome Discoverer）
2. 蛋白鉴定（FDR < 1% at PSM and protein level）
3. LFQ 或 TMT 定量
4. 缺失值过滤和插补
5. 归一化（中位数居中）
6. 差异蛋白筛选：limma 调节 t 检验（moderated t-test，与 yaml `omics.differential_analysis.proteomics` 一致；不用逐个蛋白的普通 t 检验），BH-FDR adj.p < 0.05；倍数变化阈值（如 FC > 1.5）只作预先写明的生物学意义筛选，不代替 FDR；有批次时批次进设计矩阵
7. GO 富集分析
8. KEGG 通路分析
9. PPI 网络分析（STRING）

## 基因组学 / 转录组学

1. 质控（FastQC）
2. 比对（HISAT2 / STAR）
3. 定量（featureCounts / HTSeq）
4. 差异表达（DESeq2 / edgeR / limma-voom）；有批次时把批次写进模型（如 DESeq2 `design = ~ batch + condition`），ComBat / `removeBatchEffect` 校正后的数据只用于 PCA、聚类和热图（见 yaml `omics.batch_effect`）
5. 基因集富集分析（GSEA / clusterProfiler）
6. 通路分析（KEGG / Reactome）

## 单细胞转录组（scRNA-seq）

1. **分析单位是样本**（患者 / 动物），不是细胞：同一样本的细胞彼此相关，样本量看每组有几个生物学重复，每个样本的细胞数代替不了样本数。
2. **样本间（组间 / 条件间）差异表达用 pseudobulk**：按"样本 × 细胞类型"把原始计数加总，每个样本一列，再用 DESeq2 / edgeR / limma-voom 检验，组别和批次写进设计矩阵（Squair 2021；Crowell 2020）。R：`muscat::aggregateData(sce, assay = "counts", fun = "sum", by = c("cluster_id", "sample_id"))` 后 `muscat::pbDS(pb, method = "edgeR")`。
3. 把细胞当独立样本的检验（如 Seurat `FindMarkers()` 默认的 Wilcoxon 检验）不考虑样本间的生物学变异，在两组没有真实差异时也能报出上百个"差异基因"（Squair 2021）——不能用于组间差异的推断，只用于描述细胞群的标志基因。
4. 细胞类型注释、聚类分辨率、细胞质控阈值和"细胞太少的样本 × 细胞类型组合"的排除规则，在看组间差异之前定好并写进 SAP。
5. 多重检验：每个细胞类型内 BH-FDR，写明是否再跨细胞类型校正。

参考：
- Squair JW, Gautier M, Kathe C, et al. Confronting false discoveries in single-cell differential expression. *Nat Commun*. 2021;12(1):5692. doi:10.1038/s41467-021-25960-2
- Crowell HL, Soneson C, Germain PL, et al. muscat detects subpopulation-specific state transitions from multi-sample multi-condition single-cell transcriptomics data. *Nat Commun*. 2020;11(1):6077. doi:10.1038/s41467-020-19894-4

## 多组学整合

1. 各组学层单独分析完成
2. 共有通路/基因/代谢物识别
3. 相关性分析（Spearman 跨组学层）
4. 多组学整合方法：
   - MOFA（Multi-Omics Factor Analysis）
   - mixOmics（DIABLO）
   - iCluster
5. 网络可视化（Cytoscape / NetworkX）
