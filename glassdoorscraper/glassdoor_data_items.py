# ******************************************************************************
#  Copyright (c) 2024. Vy Kauppinen (VyKp00)
# ******************************************************************************

from dataclasses import dataclass, field, InitVar
from textprocessing_utils.cleaning_text_utils import normalize_corpus


# ***** Job Class for the collected data **********
@dataclass
class JobCard:
    job_id_string: InitVar[str] = ""  # jobId is originally a string
    job_id: int = field(init=False)
    job_title: str = ""
    job_description: str = ""
    company_id: str = ""
    company_name: str = ""
    job_url: str = ""
    job_location: str = ""
    # Some company doesn't have company overview info,
    # so we'll treat all such data as strings
    company_size: str = ""
    founded_year: str = ""
    company_sector: str = ""

    # Final data constructor:
    #  * job_id: int
    #  * job_title: str
    #  * job_description: str
    #  * company_id: str
    #  * company_name: str
    #  * job_url: str
    #  * job_location: str
    #  * company_size: str
    #  * founded_year: str
    #  * company_sector: str
    def __post_init__(self, job_id_string):
        self.job_id = self.convert_id_to_string(job_id_string)
        self.job_title = self.clean_job_title()
        self.job_description = self.clean_job_description()
        self.company_id = self.company_id
        self.company_name = self.company_name
        self.job_url = self.job_url
        self.job_location = self.location_to_english()
        self.company_size = self.company_size
        self.founded_year = self.founded_year
        self.company_sector = self.company_sector
        pass

    # Convert job title to string
    def convert_id_to_string(self, job_id_string):
        return int(job_id_string)

    # Some Job title have special character and numbers
    def clean_job_title(self):
        cleaned_job_title = normalize_corpus(self.job_title,
                                             contraction_expansion=True,
                                             accented_char_removal=True, text_lower_case=False,
                                             special_char_removal=True, text_is_tech=True, remove_digits=True
                                             )
        return cleaned_job_title

    # Clean text in job description
    def clean_job_description(self):
        cleaned_job_description = normalize_corpus(self.job_description,
                                                   contraction_expansion=True,
                                                   accented_char_removal=True, text_lower_case=False,
                                                   special_char_removal=True, text_is_tech=True, remove_digits=False
                                                   )
        return cleaned_job_description

    # Some Job location has non-English letter
    def location_to_english(self):
        cleaned_location = normalize_corpus(self.job_location,
                                            contraction_expansion=False,
                                            accented_char_removal=True, text_lower_case=False,
                                            special_char_removal=True, text_is_tech=False, remove_digits=False
                                            )
        return cleaned_location
