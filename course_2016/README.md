# 2016 Course Archive

## What This Folder Is

This folder is the historical archive for the 2016 Aarhus Summer University course that shaped this project:

`Data Intensive Methods and Digital Tools for Analysis of Text Mining in R`

It keeps the original lecture materials, teaching code, project-work scripts, supporting resources, legacy result files, and raw archives in one browsable place so the repo root can stay focused on the modern public toolkit.

## How To Use This Archive

- Start with [`slides/official/`](slides/official/) if you want the core lecture deck sequence from the 2016 course.
- Go to [`code/teaching/`](code/teaching/) if you want the workshop/demo scripts that accompanied the teaching sessions.
- Go to [`code/project_work/`](code/project_work/) if you want the project-era scripts behind the children’s literature analysis.
- Go to [`resources/`](resources/) if you want the corpus specification documents and course-support files.
- Go to [`legacy_outputs/`](legacy_outputs/) if you want the archived result summaries from the original project workflow.
- Go to [`archives/raw/`](archives/raw/) if you want the original zip archives exactly as they were preserved locally.

## Program Map

The program overview is recoverable from [`legacy_repo/tm_the_great_unread_master/syllabus.tex`](legacy_repo/tm_the_great_unread_master/syllabus.tex). In short, the course moved from conceptual framing, into R foundations and preprocessing, and then into more advanced text-mining methods.

### Week 1

| Day | Main themes |
| --- | --- |
| Monday | Introduction, text analytics in the digital humanities, R basics, and the art of R |
| Tuesday | Language models, data preparation, counting words, and group work |
| Wednesday | Design and communication, sentiment analysis, and code fest |
| Thursday | Named entities, associations, and more code fest |
| Friday | Machine learning, clustering, classification, and social activities |

### Week 2

| Day | Main themes |
| --- | --- |
| Monday | Social media, business analytics, and guest material |
| Tuesday | Latent variables, network analysis, and supervision |
| Wednesday | Library sessions and corpus work |
| Thursday | Unsilo, temporal dynamics, word embedding, and supervision |
| Friday | Proposal review and wrap-up |

## Slides Table of Contents

### Official slide pack

#### `paradigm_4.pdf`

- File: [`slides/official/paradigm_4.pdf`](slides/official/paradigm_4.pdf)
- Title: `Introduction - TM the Great Unread`
- Instructor: not embedded in the PDF metadata
- Date: July 25, 2016
- Pages: 25
- TOC summary: why data-intensive science matters; the "4th paradigm" motivation; large-scale text as a humanities problem; the course rationale for text mining in the humanities and social sciences.

#### `text_analytics_in_dh.pdf`

- File: [`slides/official/text_analytics_in_dh.pdf`](slides/official/text_analytics_in_dh.pdf)
- Title: `Text Analytics (in the Digital Humanities)`
- Instructor: KLN
- Date: July 26, 2016
- Pages: 55
- TOC summary: what digital humanities is; boundary-crossing between humanities, social sciences, arts, and natural sciences; audience and social impact; project-based learning; increasing the visibility of humanities research.

#### `r_basic.pdf`

- File: [`slides/official/r_basic.pdf`](slides/official/r_basic.pdf)
- Title: `R Basics - TM the Great Unread`
- Instructor: not embedded in the PDF metadata
- Date: July 25, 2016
- Pages: 6
- TOC summary: what R is; interpreted computing and command-line use; vectors and atomic types; basic console work; factors and simple object manipulation.

#### `art_of_r.pdf`

- File: [`slides/official/art_of_r.pdf`](slides/official/art_of_r.pdf)
- Title: `The art of R - TM the Great Unread`
- Instructor: not embedded in the PDF metadata
- Date: July 25, 2016
- Pages: 4
- TOC summary: DRY programming; control structures; `if`/`else`; `for` loops; `while`/`repeat`; control-flow helpers; writing and inspecting functions.

#### `data_preparation.pdf`

- File: [`slides/official/data_preparation.pdf`](slides/official/data_preparation.pdf)
- Title: `Data Preparation`
- Instructor: Kristoffer L. Nielbo
- Date: July 19, 2016
- Pages: 6
- TOC summary: exploratory/descriptive/causal design types; iterative research design; the text-mining workflow as knowledge discovery; project-oriented data preparation.

#### `counting_words.pdf`

- File: [`slides/official/counting_words.pdf`](slides/official/counting_words.pdf)
- Title: `The Art of R - TM the Great Unread`
- Instructor: not embedded in the PDF metadata
- Date: July 26, 2016
- Pages: 6
- TOC summary: words as units of meaning; tokenization; type/token counting; frequency tables; the long-tail pattern where a few words are very frequent and most are rare.

#### `language_models.pdf`

- File: [`slides/official/language_models.pdf`](slides/official/language_models.pdf)
- Title: `Text Mining the Great Unread: Language Modeling and the NLP Pipeline`
- Instructor: Hilke Reckman
- Date: July 26, 2016
- Pages: 33
- TOC summary: overview of NLP applications; basics of n-gram models; basics of vector space models; segmentation; normalization; disambiguation; structural analysis; interpretation.

### Supplementary slide deck set

#### `design_communication.pdf`

- File: [`slides/supplementary/design_communication.pdf`](slides/supplementary/design_communication.pdf)
- Title: `Design and Communication`
- Instructor: not embedded in the PDF metadata
- Date: July 27, 2016
- Pages: 11
- TOC summary: general article structure; synopsis structure; presentation and communication guidance; course discussion/questions.

#### `sentiments.pdf`

- File: [`slides/supplementary/sentiments.pdf`](slides/supplementary/sentiments.pdf)
- Title: `Sentiments - TM the Great Unread`
- Instructor: Kristoffer L. Nielbo
- Date: July 28, 2016
- Pages: 8
- TOC summary: what sentiment analysis is; common application areas; dictionary-based methods; supervised learning; unsupervised learning; weighted lexicon scoring.

#### `latent_variables.pdf`

- File: [`slides/supplementary/latent_variables.pdf`](slides/supplementary/latent_variables.pdf)
- Title: `Latent Variable Models - TM the Great Unread`
- Instructor: not embedded in the PDF metadata
- Date: August 2, 2016
- Pages: 13
- TOC summary: topic modeling as an unsupervised mixed model; discovering thematic structure; annotating and visualizing documents; document generation from topics; reversing the generative process to infer hidden topics.

## Teaching Code Index

| File | Purpose |
| --- | --- |
| [`code/teaching/r_basics.R`](code/teaching/r_basics.R) | Introductory R examples aligned to the R basics teaching session |
| [`code/teaching/art_of_r.R`](code/teaching/art_of_r.R) | Demonstrations of control flow, functions, and cleaner R programming habits |
| [`code/teaching/data_preparation.R`](code/teaching/data_preparation.R) | Early data extraction and preprocessing examples for text-mining workflows |
| [`code/teaching/counting_words.R`](code/teaching/counting_words.R) | Word counting, token-frequency, and simple corpus statistics examples |

## Project Work Index

| File | Purpose |
| --- | --- |
| [`code/project_work/Cleaning_metadata_from_Gutenberg_Corpus.r`](code/project_work/Cleaning_metadata_from_Gutenberg_Corpus.r) | Strip Gutenberg boilerplate and tokenize text collections |
| [`code/project_work/Updated_project_script.r`](code/project_work/Updated_project_script.r) | Main rough project script for the children’s literature final project |
| [`code/project_work/scraping.R`](code/project_work/scraping.R) | Download Gutenberg texts from bookshelf/source pages |
| [`code/project_work/sentiment_gender.R`](code/project_work/sentiment_gender.R) | Run sentiment analysis over gendered corpora and text slices |
| [`code/project_work/util_fun.R`](code/project_work/util_fun.R) | Small helper utilities reused by the project scripts |
| [`code/project_work/data_preparation.R`](code/project_work/data_preparation.R) | Alternative preprocessing script for a local working setup |
| [`code/project_work/data_preparation (1).R`](code/project_work/data_preparation%20%281%29.R) | Variant preprocessing script using a different local path convention |
| [`code/project_work/Java.R.troubleshooting.R`](code/project_work/Java.R.troubleshooting.R) | Setup notes for fixing `rJava` issues on macOS during the original workflow |

## Supplementary Resources Index

### Corpus specification documents

| File | Purpose |
| --- | --- |
| [`resources/corpus_specs/Corpus of gold.docx`](resources/corpus_specs/Corpus%20of%20gold.docx) | Canonical 20-book children’s literature list used as the legacy core corpus |
| [`resources/corpus_specs/Corpus of gold-2.docx`](resources/corpus_specs/Corpus%20of%20gold-2.docx) | Duplicate/alternate preserved copy of the same corpus specification |

### Course support files

| File | Purpose |
| --- | --- |
| [`resources/course_support/Important Book R.pdf`](resources/course_support/Important%20Book%20R.pdf) | Reference book on Singular Spectrum Analysis with R kept with the course materials |
| [`resources/course_support/stoplist.csv`](resources/course_support/stoplist.csv) | Stopword/support list used in course-era processing |
| [`resources/course_support/kjv_metadata.csv`](resources/course_support/kjv_metadata.csv) | Metadata table for the KJV support corpus |
| [`resources/course_support/kjv.RData`](resources/course_support/kjv.RData) | R workspace/support object related to the KJV materials |

## Legacy Outputs Index

| File | Purpose |
| --- | --- |
| [`legacy_outputs/data.txt`](legacy_outputs/data.txt) | Archived console/result output from the original workflow |
| [`legacy_outputs/data-2.txt`](legacy_outputs/data-2.txt) | Alternate archived output block from the original workflow |
| [`legacy_outputs/t_models.txt`](legacy_outputs/t_models.txt) | Topic-model notes/results from the legacy analysis |
| [`legacy_outputs/final_t_models.txt`](legacy_outputs/final_t_models.txt) | Later topic-model result summary from the legacy analysis |
| [`legacy_outputs/english1.dat`](legacy_outputs/english1.dat) | Legacy auxiliary data file used in the original analysis context |
| [`legacy_outputs/loading_the_directory_and_most_cleaning.txt`](legacy_outputs/loading_the_directory_and_most_cleaning.txt) | Working notes on loading directories and performing the bulk of legacy cleaning |

## Raw Archives Index

| File | Purpose |
| --- | --- |
| [`archives/raw/slides-2016-07-26.zip`](archives/raw/slides-2016-07-26.zip) | Original archived slide bundle from July 2016 |
| [`archives/raw/code-2016-07-26.zip`](archives/raw/code-2016-07-26.zip) | Original archived teaching-code bundle from July 2016 |
| [`archives/raw/data-2016-07-26.zip`](archives/raw/data-2016-07-26.zip) | Original archived course data bundle from July 2016 |
| [`archives/raw/other_resources-2016-07-26.zip`](archives/raw/other_resources-2016-07-26.zip) | Original archived support-resource bundle from July 2016 |

## Legacy Repo Snapshot

| File | Purpose |
| --- | --- |
| [`legacy_repo/tm_the_great_unread_master/README.md`](legacy_repo/tm_the_great_unread_master/README.md) | Historical top-level README for the original course repo |
| [`legacy_repo/tm_the_great_unread_master/syllabus.tex`](legacy_repo/tm_the_great_unread_master/syllabus.tex) | Full syllabus/program overview used for the course |
| [`legacy_repo/tm_the_great_unread_master/r_basics.R`](legacy_repo/tm_the_great_unread_master/r_basics.R) | Original repo copy of the R basics teaching script |
| [`legacy_repo/tm_the_great_unread_master/art_of_r.R`](legacy_repo/tm_the_great_unread_master/art_of_r.R) | Original repo copy of the art-of-R teaching script |
