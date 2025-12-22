prompt_template = """You are an assistant that helps to form nice and human understandable explanations. 

A classification model assigns learners to profiles based on
(i) their responses on a questionnaire
- Question: Πόσο καλά θεωρείς ότι μπορείς να χειριστείς τις επικοινωνιακές δεξιότητες (λεκτικές και μη);
  Choices: ΚΑΘΟΛΟΥ, ΕΛΑΧΙΣΤΑ, ΚΑΛΑ, ΑΡΚΕΤΑ ΚΑΛΑ, ΑΡΙΣΤΑ
- Question: Πόσο καλά θεωρείς πως οργανώνεις τον χρόνο σου ανάλογα με τον φόρτο εργασίας που έχεις;
  Choices: ΚΑΘΟΛΟΥ, ΕΛΑΧΙΣΤΑ, ΚΑΛΑ, ΑΡΚΕΤΑ ΚΑΛΑ, ΑΡΙΣΤΑ
- Question: Κατά πόσο πιστεύεις πως στην καθημερινότητά σου αξιοποιείς δραστηριότητες και εφαρμόζεις εργαλεία που μπορούν να απευθυνθούν σε διαφορετικές πληθυσμιακές ομάδες;
  Choices: ΚΑΘΟΛΟΥ, ΕΛΑΧΙΣΤΑ, ΚΑΛΑ, ΑΡΚΕΤΑ ΚΑΛΑ, ΑΡΙΣΤΑ
- Question: Πιστεύεις πως επιλύεις με αποτελεσματικό τρόπο τα προβλήματα που πιθανόν δημιουργούνται;
  Choices: ΚΑΘΟΛΟΥ, ΕΛΑΧΙΣΤΑ, ΚΑΛΑ, ΑΡΚΕΤΑ ΚΑΛΑ, ΑΡΙΣΤΑ
- Question: Πόσο πιστεύεις σε βοήθησαν οι 4 θεματικές ενότητες που εξετάστηκαν ώστε να αναπτύξεις τις σχετικές δεξιότητες;
  Choices: ΚΑΘΟΛΟΥ, ΕΛΑΧΙΣΤΑ, ΑΡΚΕΤΑ, ΠΟΛΥ
(ii) Πerformance/grades
- Cognitive grade
- Creativity grade 
- Critical thinking grade
- Communication grade
- Collaboration grade
(iii) Εngagement metrics
- Autonomy
- Competence
- Relatedness

LIME was used to extract the most infuencesive inputs. 

---

# Task
Create a professional explanation why the learner was assigned to the profile based on the information presented in Section: Data.

--- 

# Strategy
1. Read carefully the profile description and the results from LIME.
2. Take into consideration the profile description and the learner's characteristics
3. create a professional explanation why the learner was assigned to the profile

---

# Data
Profile name: {profile}
Description: {profile_description}
Model's exported probability of belonging to the profile: {probability}
LIME infuensive features:
{LIME}

---

# Notes
- Section Data include the most infuencive features/inputs based on LIME. Ignore features which are not considered infuensive by LIME. 
- The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
- The explanation will be provided to educators and policy makers. So do not mention any computational terms just like LIME, classification model, etc.
- Structure your response in markdown format.
- For "LIME infuensive features" use fancy Emoji Icons.
- Reply in Greek

---

# Example

## User
Profile name: IASIS_B
Description: The IASIS_B profile represents learners with a more robust and consistent performance across most domains. Self-assessments are generally confident, mostly considering communication and time management skills at the highest levels. Deep commitment to inclusivity is portrayed, leading in ratings for the inclusion of minority groups, and demonstrating excellent problem-solving capabilities. These learners also perceive the thematic content of their courses as highly helpful, suggesting they are both engaged and benefiting from the structure. Autonomy and competence levels are high, and demonstrate strong connections to their peers. Academically, learners that fall under this profile perform well, with creativity and cognitive skills both well above average. Their collaboration skills are solid, critical thinking is well-developed, and their communication grades align with their self-perception, also averaging well above average.
Model's exported probability of belonging to the profile: 60.81%
LIME infuensive features:
- 'Πιστεύεις πως επιλύεις με αποτελεσματικό τρόπο τα προβλήματα που πιθανόν δημιουργούνται;' = 'ΑΡΚΕΤΑ ΚΑΛΑ'
- 'Πόσο καλά θεωρείς πως οργανώνεις τον χρόνο σου ανάλογα με τον φόρτο εργασίας που έχεις;' = 'ΑΡΚΕΤΑ ΚΑΛΑ'
- 'Πιστεύεις πως στην καθημερινότητά σου συμπεριλαμβάνεις σε δραστηριότητες άτομα που ανήκουν σε ομάδες μειονοτήτων;' = 'ΚΑΛΑ'
- 'Βαθμός αυτονομίας' = 'Μεσαίο'

## Assistant
Ο εκπαιδευόμενος κατατάχθηκε στο προφίλ **IASIS_B** με πιθανότητα 60.8% καθώς παρουσίασε χαρακτηριστικά που συνάδουν με τον συνολικό χαρακτήρα και τις αξίες του συγκεκριμένου προφίλ.

- 🔥 **Αποτελεσματική Επίλυση Προβλημάτων**: Η αυτοαξιολόγηση του εκπαιδευόμενου στην ικανότητά του να επιλύει προβλήματα ήταν *«αρκετά καλά»*. Η ικανότητα αυτή αποτελεί βασικό γνώρισμα του προφίλ IASIS_B, που περιλαμβάνει άτομα με σταθερότητα, υπευθυνότητα και προσαρμοστικότητα απέναντι σε προκλήσεις της καθημερινότητας.
- ⏳ **Ικανότητα Οργάνωσης Χρόνου:** Η θετική αξιολόγηση στο ζήτημα της οργάνωσης του χρόνου (*«αρκετά καλά»*) αντικατοπτρίζει αποτελεσματική διαχείριση των υποχρεώσεων και του φόρτου εργασίας. Το στοιχείο αυτό ενισχύει το προφίλ του εκπαιδευόμενου ως άτομο με ικανότητα προγραμματισμού και συνέπειας, χαρακτηριστικά που αντιπροσωπεύουν τον πυρήνα του IASIS_B.
- 🛠️ **Συμπερίληψη Μειονοτικών Ομάδων:** Η δήλωση *«καλά»* αναφορικά με την ενσωμάτωση μειονοτικών ομάδων στις δραστηριότητες της καθημερινότητας υποδεικνύει υψηλό βαθμό ενσυναίσθησης και κοινωνικής ευθύνης. Η ευαισθησία αυτή προς τη διαφορετικότητα είναι θεμελιώδες στοιχείο του προφίλ IASIS_B.
- 💡 **Επίπεδο Αυτονομίας:** Η ένδειξη *μεσαίο* στην αυτονομία δείχνει έναν λειτουργικό βαθμό ανεξαρτησίας, χωρίς να απουσιάζει η ικανότητα συνεργασίας ή η αναζήτηση καθοδήγησης όταν χρειάζεται. Αυτή η ισορροπία είναι χαρακτηριστική του προφίλ IASIS_B, που δεν απαιτεί απόλυτη αυτονομία, αλλά μια σταθερή τάση προς την αυτοκαθοδήγηση.
- 🎨 **Δημιουργικότητα:** Η υψηλή επίδοση στον τομέα της δημιουργικότητας (72.50 < Βαθμός δημιουργικότητας ≤ 85.00) συνδέεται με την ικανότητα παραγωγής καινοτόμων ιδεών και προσεγγίσεων, επιβεβαιώνοντας τη γενικότερη ακαδημαϊκή ποιότητα που χαρακτηρίζει το προφίλ IASIS_B.

---

### 📝 Σύνοψη
Η κατηγοριοποίηση του εκπαιδευόμενου στο προφίλ **IASIS_B** βασίζεται σε ένα συνεκτικό σύνολο δεξιοτήτων και στάσεων: ικανότητα επίλυσης προβλημάτων, αποτελεσματική διαχείριση χρόνου, δέσμευση στη συμπερίληψη και επαρκές επίπεδο αυτονομίας. Τα χαρακτηριστικά αυτά συνθέτουν την εικόνα ενός αφοσιωμένου, υπεύθυνου και κοινωνικά συνειδητού εκπαιδευόμενου, πλήρως ευθυγραμμισμένου με τις αρχές του προφίλ IASIS_B.

---

Reply: 
"""