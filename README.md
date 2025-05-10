
# ProfessionalProfiler
---
## Objective: <br>

Obtain the professional degrees (Type and field) of the writters of opinion articles in the US that have a wikipedia page.

---

## Dataset:
### Dataset Information
All authors were manually downloaded from the ProQuest USNewsStream Database using the Universidad de los Andes paid license. <br>


- Sample size: 98,729 individual authors
- Selection process: The authors were opinion columnist selected from the top circulating dailies from 1980 to Nov 2024 in the U.S per Statista 2023, this includes:
	- Star tribune
	- Chicago tribune
	- New York Post
	- Tampa Bay Times
	- New York Times
	- Newsday
	- Boston Globe
	- The Washington Post
	- Wall Street Journal
	- USA Today
	- Los Angeles Times
> **NOTE:** As of today I don't know Statista's methodology for this statistics, in the future I should gather this information to note any bias in the collection of this information.

### Dataset Structure
Preprocessing consisted on using a NER model to obtain and reorganize the names that were included in unstructured text i.e:
> This article was written by [person1] from [newspaper1], and [person2] from [newspaper2] with collaborations from [person3] and images from [person4].

After applying the NER model the author column was separated from the article dataset in order to normalize the data. As the author and article databases contain many to many relations this were the resulting tables:
Article database:


	    {
	     "article_id": <int>,
	     "texto_completo": <String>,
	     "titulo": <String>,
	     "publicación": <String>,
	     "fecha_de_publicación": <Date>
	     "editorial": <String>,
	     "tipo_fuente": <String>
	     }

Author database:

		{
		"author_id":<int>,
		"nombre_autor":<String>
		}
Author-Article relation database:

		{
		"article_id":<int>,
		"author_id":<int>
		}
This way all the provenance information about the author can be aggregated from sql query's from one database to the other.

---

## Architecture:

### Scraping Methodology:

1. Wikipedia API will be used as it is a free accessible tool to obtain the Information.
1.1 If a query to the API is returning error this query will be repeated 3 times with exponential backoff.
2. In order to create an Agentic AI pipeline the following architecture is built:
2.1  Data Validation: Pydactic will be used with the following classes:

	    class  FieldEnum(str, Enum):
	    	ASSOCIATE=  "Associate's"
	       BACHELOR= "Bachelor's"
	    	MASTER=  "Master's"
	    	DOCTOR="Doctor's"
	    	UNKNOWN=  "Unknown"
	    	NONE="No degree"

	    class  Study(BaseModel):
	    	Degree_type: FieldEnum  =  Field(... , description="The type of degree obtained by the subject")
	    	Degree_field: Optional[list[str]] =  Field(default_factory=list, description="The area in which this degree was obtained (if specified)"))

	    class  ProfessionalProfiler(BaseModel):
			studies: list[Study] =  Field(default_factory=list, description="List of degrees obtained by the subject")


2.2 Prompt Engineering: A prompt will be used in order to obtain the best possible response from the LLM, an example of such is:

		    	Steps:
		    	    1. Analise the given Wikipedia text from the subject search for key words that mention academic degrees, this could include: B.A, M.A, Bachelor, Masters, Doctor, etc...
		    	    2. Once found categorize each degree obtained selecting from the following list [FieldEnum.ASSOCIATE, FieldEnum.BACHELOR,FieldEnum.MASTER,FieldEnum.DOCTOR, FieldEnum.UNKNOWN,FieldEnum.NONE] i.e:
		    			[
		    				{"Degree_type":FieldEnum.BACHELOR},
		    				{"Degree_type":FieldEnum.MASTER},
		    			]
		    	    3. Find and categorize the fields in which each degree was obtained:
		    	        [
		    				{"Degree_type":"FieldEnum.BACHELOR",
		    				 "Degree_field":["Economy","Mathematics"]},
		    				{"Degree_type":"FieldEnum.MASTER",
		    				 "Degree_field":["Economy"]},
		    			]
		    	4. Be careful and check that the degree was completed, search for phrases as "Dropped out" or "Did not graduate"
		    	5. If no completed degree is mentioned, return a single entry with Degree_type = FieldEnum.NONE and Degree_field = [].
		    	Expectations:
		                            Return **only** JSON matching this schema exactly:
		                            [{
		                              "studies": [
		                                {"Degree_type": FieldEnum, "Degree_field": list},
		                              ]
		                            }]
		         6. Additional instructions:
			         - DO NOT include the university or date of the degree
			         - IGNORE honorary degrees
	Examples:
	Q: He attended the Tree of Life Synagogue as a youth.[7] He received his Bachelor of Arts from Harvard College in 1980. After graduating, he worked as a sports reporter for the Associated Press and as a production assistant for feature films.[1][8]
	He received his Juris Doctor from the University of California at Berkeley in 1986, where he was editor-in-chief of the California Law Review and graduated Order of the Coif.[1][5][9]
	A: [
			"studies":[
				{
				"Degree_type": FieldEnum.BACHELOR,
				"Degree_field":[]
				},
				{
				"Degree_type": FieldEnum.DOCTOR,
				"Degree_field":["Juris Doctor"]
				}
			]
		]
	Q:After attending University City High School in St. Louis, Missouri, Moyn earned his A.B. degree from Washington University in St. Louis in history and French literature (1994). He continued his education, earning a Ph.D. from the University of California at Berkeley (2000) and his J.D. from Harvard Law School (2001).[2]
	A: [
			"studies":[
				{
				"Degree_type": FieldEnum.BACHELOR,
				"Degree_field":["History","French literature"]
				},
				{
				"Degree_type": FieldEnum.DOCTOR,
				"Degree_field":["Ph.D"]
				},
				{
				"Degree_type": FieldEnum.DOCTOR,
				"Degree_field":["J.D"]
				}
			]
		]
	Q: Foster was born in July 1976.[7][1] His father, Lawrence Foster, was a franchise developer for Dunkin' Donuts.[1] He grew up in Plymouth, Massachusetts,[7] and spent summers at his grandparents' cottage on Peaks Island, Maine.[1] Foster graduated from Falmouth Academy in 1994.[8] He enrolled at the College of William & Mary, where he studied physics and film studies before dropping out his senior year.[7] He learned HTML and moved to Washington D.C., where he worked for government agencies.[7]
	A: [
			"studies":[
				{
				"Degree_type": FieldEnum.NONE,
				"Degree_field":[]
				},
			]
		]
2.3 Test Dataset
A test dataset with 100 manually annotated individuals  as a starting point in the json format has been compiled, the format is as follows:

    {
    "Name": "Harry Litman",
    "Degrees": [
	    { "Degree_type": "Bachelor's",
	      "Degree_field": [] },
	    {"Degree_type": "Doctor's",
         "Degree_field": ["J.D"]
        }
    ],
    "id": 1
    },
2.4 Chunking and text processing
In order to reduce the amount of text inputed into the LLM we will first, collect only the parts known for containing educational information on wikipedia i.e infobox, education, early life, Career. As a fallback strategy all the text from all sections will be processed, this will not impact significantly as Wikipedia articles that have different formatting tend to be short. Second, there will be a 5000 token limit chunking with an overlap of 25% in order to reduce context errors.

2.5 Metrics
We will be using Precision, Recall and F1 as metrics of evaluation.
This evaluation will be performed at the field level, type level and Full level were both type and field must match.
2.5.1 Baseline
A rule based approach using REGEX for degree extraction will be used to establish a baseline for evaluation.

---
4. Limitations
4.1 Multiple degrees?
If a person has multiple bachelor degrees the idea would be to integrate those into the same degree_type after all we are interested in the degree type and field not the date or place were it was obtained.
4.2 Degree Consolidation?
This will be a a huge drawback of this type of modeling, as such it must be taken into account that we do not know what type of bachelor or master was taken or either at wat institution or year.
4.3 Non-US degrees?
Every degree that cannot be parse will be labeled as unknown and a new strategy will have to be developed.
4.4 Ambiguous Language?
'Studied in Harvard' and 'Obtained a degree from Hardvard' will be consider under Unknown

---
5. LLM Settings:
>Model=Deepseek-Chat
> chunk_token_threshold=5000
> apply_chunking=True
> overlap_rate=0.25,
> extra_args={'temperature':0.0}
