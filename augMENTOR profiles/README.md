# augMENTOR profiles

This folder includes the pipelines for the development of the augMENTOR profiles (T5.2). The challanges of this task are

- grouping/clustering of learners based on selected features
- provide explanability why a learner was assigned to one of the pre-defined profiles

For addressing these challenges, we developed a methodology, which is depicted in the following figure:

1. Load raw data
2. Feature Selection
3. Perform clustering (fine-tuning + evaluation)
4. Label the dataset using the developed clusters
5. Train a classifier, eg Random Forest, on the labeled dataset (fine-tuning + evaluation) 
6. Employment of explainability techniques, eg LIME

<br />

<p align="center">
<img src=".\images\augMENTOR_profiles.png" width = "1000" alt="" align=center />
</p>

<br />

## augMENTOR profiles pipelines

### Generation of augMENTOR profiles

The data from questionnaires together with learner's performance data and engagement metrics for each learner are gathered, correlated and indexed. 
After the data are pre-processed (check for non-valid values, imputation for handling NaN values) are imported to the `Feature selection` module in which is based on the application of the FRUITS algorithm [(Zhang & Zhao, 2009)](#1) for feature selection.

Next, the selected learner's data are imported to the `Clustering` module, which performs the following actions
- Scaler application (standarization/normalization/etc)
- Dimensionality reduction (UMAP) to reduce variance
- Application of clustering algorithm: Gaussian mixture models (GMM)

The output of this module are the generated augMENTOR profiles for each pilot

<p align="center">
<img src=".\images\Create_profiles.png" width = "1000" alt="" align=center />
</p>

### Learner's assignment to the augMENTOR profiles

For the learner's assignment to the augMENTOR profiles, the development of clustering model and explanability functionality is considered essential.

Initially, a labeled data is generated, which is composed by the learner's selected data (questionnaires, features related to learners' performance and engagement metrics), correlated with the augMENTOR profiles (labels). This dataset is imported to the `Training classification model`, which trains a Random Forest (RF) classifier. Notice that the RF is tuned for optimizing its performance.

Finaly, the trained model is able to assign each learner to one of the pre-defined augMENTOR profiles; while the application of `augMENTOR profiles explainability` module provides an explanation about each assignment. Specifically, in this model the Local Interpretable Model-agnostic Explanations (LIME) proposed by [Mishra et al., 2017](#2) is employed for obtaining the explanation about the RF predictions

    
<p align="center">
<img src=".\images\Assign_to_profiles.png" width = "1000" alt="" align=center />
</p>

<br/>

### Modules' description

> Feature selection

**Input**

- Data: Learners' data (questionnaire, performance metrics, engagement metrics)

**Output**

- Selected data



> Clustering

**Input**

- Data: Learners' data 

**Output**

- augMENTOR profiles (clusters)


> Training classification model

**Input**

- Labeled data: learners' data correlated with augMENTOR profiles (labels)

**Output**

- Trained model


> augMENTOR profiles explainability

**Input**

- Data: (questionnaire, performance metrics, engagement metrics)
- Model: prediction models, which assigns learners to the pre-defined augMENTOR profiles

**Output**

- Explanation about each assignment 

<br/>


## Information about augMENTOR profiles implementation

### Engagement metrics

The engagement metrics: 'Autonomy', 'Competence', 'Relatedness' are categorical features taking the following values: ['Low', 'Medium', 'High', 'Very high']. Moreover, they are defined as the sum of the following categorical sub-features:

- **Autonomy**
   - Number of submissions (Scrom)
   - Number of completed attempts (Scrom)
   - Number of posts (Forum)
   - Number of discussions (Forum)
- **Competence**
   - Quiz grade (Quiz)
   - Number of discussions (Forum)
- **Relatedness**
   - Number of posts (Forum)
   - Number of submissions (Forum)
   - Number of discussions (Forum)

which take values in ['Low', 'Medium', 'High', 'Very high']. Notice that the binning ranges for assigning the values on the sub-features are tailored per pilot, after performing a statistical analysis on the collected pre-pilot data.

Finally, it is worth mentioning that the engagement metrics were preferred to be categorical (binning strategy) for the following reasons:

1. **Improved interpretability:** Binning converts numerical values into discrete categories that are easier to understand and interpret for non-technical stakeholders, such as educators or administrators.

2. **Simplification of analysis:** Discrete categories simplify clustering or decision-making processes, especially when working with qualitative assessments or ordinal comparisons. It reduces the noise from slight variations in numerical values that might not significantly impact the overall categorization.

3. **Better compatibility with certain models:** Some clustering methods (e.g., k-modes) and rule-based approaches work better with categorical data than with continuous values.
It avoids complications associated with standardization or normalization of continuous data.

4. **Reduced sensitivity to measurement errors:** Small variations or inaccuracies in the original [0,1] scale (e.g., due to rounding or measurement error) become less impactful when values are grouped into broader categories.

5. **Alignment with educational frameworks:** Binning aligns more closely with educational practices that often use categorical grades or descriptive levels (e.g., 'Exceeds Expectations'). It allows easier integration into existing grading and assessment frameworks, making results actionable for educators.


### Pipeline 

Firstly, the data is retrieved directly from MOODLE (notice that the learners' information are retrieved from the KG due to simplicity).  Then, the data are

1. Pre-process to be converted to the proper form (include imputation)
    - check for non-valid values
    - imputation for handling NaN values
2. Unsupervised feature selection using FRUITS algorithm [(Zhang & Zhao, 2009)](#1). 
3. Application of data scaler (normalization/standarization/etc)
4. Dimensionality reduction (UMAP) to reduce variance
5. Application of clustering algorithms
    - Several algorithms were utilized; however, the best performance was reported by Gaussian mixture models (GMM)
    - Clustering evaluation (can be found in the corresponding notebook)
        - Using performance metrics: Silhoutte score, Calinski-Harabasz and Davies-Bouldin 
        - 2D-visualization
        - Cluster analysis (histograms for nominal variables and boxplot for real variables)
        - Application of apriori algorithm for possible extraction of rules for assisting clustering analysis
6. Development of clustering model and explanability functionality
    - Development of a labeled dataset (clusters as used as labels)
    - Training a RF classifier (The fine-tuning of the classifier can be performed using nb: `02.FineTuning (RandomForest).ipynb`)
    - Utilization of Local Interpretable Model-agnostic Explanations (LIME) proposed by [Mishra et al., 2017](#2) for providing local explainability information


<br/>

### Explainability functionality

**Motivation**: Include an explaination why a learner was assigned to a augMENTOR profile

**Problem**: Clustering algorithm do not offer local explainability 

**Proposed approach**: After the data are clustered using one of the mentioned approaches, a classifier is trained and fine-tuned on a labeled data, composed by the synthetic data and as label the cluster. This methodology includes the assignment of a new instance to a cluster based NOT on the clustering model/pipeline but using a trained classifier. The advantage of this approach is exploit the trained classifier along with Local Interpretable Model-agnostic Explanations (LIME) for providing global and local explainability.

<br/>


## References

<a id="1">[1]</a>  Zhang, F., & Zhao, Y. J. (2009, July). Unsupervised feature selection based on feature relevance. In 2009 International Conference on Machine Learning and Cybernetics (Vol. 1, pp. 487-492).

<a id="2">[2]</a>  Mishra, S., Sturm, B. L., & Dixon, S. (2017). Local interpretable model-agnostic explanations for music content analysis. In ISMIR (Vol. 53, pp. 537-543).