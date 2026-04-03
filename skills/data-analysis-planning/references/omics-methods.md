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
9. 模型验证：置换检验（n=200）、CV-ANOVA
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
6. 差异蛋白筛选（limma / t-test，FC > 1.5, adj.p < 0.05）
7. GO 富集分析
8. KEGG 通路分析
9. PPI 网络分析（STRING）

## 基因组学 / 转录组学

1. 质控（FastQC）
2. 比对（HISAT2 / STAR）
3. 定量（featureCounts / HTSeq）
4. 差异表达（DESeq2 / edgeR / limma-voom）
5. 基因集富集分析（GSEA / clusterProfiler）
6. 通路分析（KEGG / Reactome）

## 多组学整合

1. 各组学层单独分析完成
2. 共有通路/基因/代谢物识别
3. 相关性分析（Spearman 跨组学层）
4. 多组学整合方法：
   - MOFA（Multi-Omics Factor Analysis）
   - mixOmics（DIABLO）
   - iCluster
5. 网络可视化（Cytoscape / NetworkX）
