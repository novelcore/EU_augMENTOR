import pandas as pd
import numpy as np
import mysql.connector
from collections import Counter
from utils.neo4j_connection import Neo4jConnection
from datetime import datetime, timedelta
from collections import Counter
from utils.utils import format_time, compute_histogram_bins, calculate_trent
from utils.engagement_utils import retrieve_learner_interactions

d_threshold = {'UPAT': {'low': 2.5, 'high': 7.5},
               'IASIS': {'low': 4, 'high': 8.2},
               'EASD': {'low': 1.2, 'high': 2.6},
               'KTU': {'low': 2.5, 'high': 7.5}, # TODO
               }

# Language translations
translations = {
    'greek': {
        'quiz_statistics': 'Στατιστικά',
        'module_statistics': 'Στατιστικά για δραστηριότητες Quiz',
        'total_quizzes': 'Σύνολο Quiz',
        'total_learners': 'Σύνολο Μαθητών',
        'completion_rate': 'Συνολικό Ποσοστό Ολοκλήρωσης',
        'avg_attempts': 'Μέσος Όρος Προσπαθειών ανά Μαθητή',
        'max_attempts': 'Μέγιστες Προσπάθειες από Έναν Μαθητή',
        'multiple_attempts': 'Μαθητές με Πολλαπλές Προσπάθειες',
        'peak_activity_hour': 'Ώρα Μέγιστης Δραστηριότητας',
        'peak_activity_day': 'Ημέρα Μέγιστης Δραστηριότητας',
        'action_distribution': 'Κατανομή Ενεργειών',
        'attempt_distribution': 'Κατανομή Προσπαθειών',
        'attempt_s': 'προσπάθεια(ες)',
        'learner_behavior': 'Συμπεριφορά & Επιδόσεις Μαθητών',
        'grades': 'Βαθμολογίες',
        'cognitive': 'Γνωστικό',
        'communication': 'Επικοινωνία',
        'creativity': 'Δημιουργικότητα',
        'critical_thinking': 'Κριτική σκέψη',
        'collaboration': 'Συνεργασία',
        'learner_type_distribution': 'Κατανομή Τύπου Μαθητή',
        'engagement_metrics': 'Μετρήσεις Εμπλοκής',
        'avg_completion_per_user': 'Μέσος όρος ολοκλήρωσης προσπαθειών ανά χρήστη',
        'avg_time_per_user': 'Μέσος χρόνος ανά χρήστη',
        'avg_actions_per_user': 'Μέσες ενέργειες ανά χρήστη',
        'decreasing_time': 'Μαθητές με Μειωμένο Χρόνο Ολοκλήρωσης σε Προσπάθειες',
        'struggle_analysis': 'Ανάλυση Δυσκολίας του Quiz με βάση την απόδοση των μαθητών',
        'learners': 'μαθητών',
        'learner_engagement_profile': 'Προφίλ Εμπλοκής Μαθητή',
        'learner_type': 'Τύπος Μαθητή',
        'total_attempts': 'Σύνολο Προσπαθειών',
        'completed_attempts': 'Ολοκληρωμένες Προσπάθειες',
        'total_time_spent': 'Συνολικός Χρόνος',
        'avg_time_per_attempt': 'Μέσος Χρόνος ανά Προσπάθεια',
        'improving_efficiency': 'Βελτίωση Αποδοτικότητας/Μείωση χρόνου σε προσπάθειες',
        'yes': 'Ναι',
        'no': 'Όχι',
        'action_frequency': 'Συχνότητα Ενεργειών',
        'attempt_details': 'Λεπτομέρειες Προσπαθειών',
        'start_attempt': 'Έναρξη',
        'end_attempt': 'Τερματισμός',
        'attempt': 'Προσπάθεια',
        'completed': 'Ολοκληρώθηκε',
        'not_completed': 'Δεν ολοκληρώθηκε',
        'duration': 'Διάρκεια',
        'learning_resources': 'Πόροι μάθησης που έγιναν προσπελάσιμοι κατά τη διάρκεια της προσπάθειας',
        # Days of the week
        'Monday': 'Δευτέρα',
        'Tuesday': 'Τρίτη',
        'Wednesday': 'Τετάρτη',
        'Thursday': 'Πέμπτη',
        'Friday': 'Παρασκευή',
        'Saturday': 'Σάββατο',
        'Sunday': 'Κυριακή',
        # Learner categories
        'one_shot_quick_quiz_completer': 'Γρήγορη Ολοκλήρωση Κουίζ με Μία Προσπάθεια',
        'incomplete_single_attempt_learner': 'Μαθητής με Μη Ολοκληρωμένη Μοναδική Προσπάθεια',
        'improving_multi_attempt_quiz_performer': 'Βελτιωτική Απόδοση με Πολλαπλές Προσπάθειες',
        'consistent_multi_attempt_quiz_performer': 'Σταθερή Απόδοση με Πολλαπλές Προσπάθειες',
        'high_effort_struggling_quiz_learner': 'Προσπάθεια με Δυσκολία και Υψηλό Κόπο',
        'low_engagement_disengaged_quiz_learner': 'Χαμηλή Εμπλοκή και Αποσύνδεση από το Κουίζ',
        'inconsistent_partial_quiz_performer': 'Μη Σταθερή Επίδοση με Μερική Ολοκλήρωση',
        'unclassified': 'Μη Κατηγοριοποιημένος',
        # Difficulty levels
        'Low': 'Χαμηλό',
        'Medium': 'Μέτριο',
        'High': 'Υψηλό',
        # Actions
        'autosaved': 'Αυτόματη αποθήκευση (autosaved)',
        'viewed': 'Προβολή (viewed)',
        'uploaded': 'Μεταφόρτωση (uploaded)',
        'updated': 'Ενημέρωση (updated)',
        'reviewed': 'Επανεξέταση (reviewed)',
        'replied': 'Απάντηση (replied)',
        'started': 'Έναρξη (started)',
        'submitted': 'Υποβολή (submitted)',
        'removed': 'Αφαίρεση (removed)',
        'created': 'Δημιουργία (created)',
        'accepted': 'Αποδοχή (accepted)',
        'graded': 'Βαθμολόγηση (graded)',
    },
    'serbian': {
        'quiz_statistics': 'Statistike',
        'module_statistics': 'Statistike o Quiz aktivnostima',
        'total_quizzes': 'Ukupno kvizova',
        'total_learners': 'Ukupno učenika',
        'completion_rate': 'Ukupna stopa završavanja',
        'avg_attempts': 'Prosečan broj pokušaja po učeniku',
        'max_attempts': 'Maksimalni broj pokušaja od jednog učenika',
        'multiple_attempts': 'Učenici sa više pokušaja',
        'peak_activity_hour': 'Vreme najveće aktivnosti',
        'peak_activity_day': 'Dan najveće aktivnosti',
        'action_distribution': 'Distribucija akcija',
        'attempt_distribution': 'Distribucija pokušaja',
        'attempt_s': 'pokušaj(a)',
        'learner_behavior': 'Ponašanje i performanse učenika',
        'grades': 'Ocene',
        'cognitive': 'Kognitivno',
        'communication': 'Komunikacija',
        'creativity': 'Kreativnost',
        'critical_thinking': 'Kritičko mišljenje',
        'collaboration': 'Saradnja',
        'learner_type_distribution': 'Distribucija tipova učenika',
        'engagement_metrics': 'Metrije angažovanja',
        'avg_completion_per_user': 'Prosečno završavanje pokušaja po korisniku',
        'avg_time_per_user': 'Prosečno vreme po korisniku',
        'avg_actions_per_user': 'Prosečne akcije po korisniku',
        'decreasing_time': 'Učenici sa smanjenim vremenom završavanja kroz pokušaje',
        'struggle_analysis': 'Analiza poteškoća',
        'learners': 'učenika',
        'learner_engagement_profile': 'Profil angažovanja učenika',
        'learner_type': 'Tip učenika',
        'total_attempts': 'Ukupno pokušaja',
        'completed_attempts': 'Završeni pokušaji',
        'total_time_spent': 'Ukupno vreme',
        'avg_time_per_attempt': 'Prosečno vreme po pokušaju',
        'improving_efficiency': 'Poboljšanje efikasnosti/Smanjenje vremena kroz pokušaje',
        'yes': 'Da',
        'no': 'Ne',
        'action_frequency': 'Frekvencija akcija',
        'attempt_details': 'Detalji pokušaja',
        'start_attempt': 'Početak',
        'end_attempt': 'Završetak',                        
        'attempt': 'Pokušaj',
        'completed': 'Završeno',
        'not_completed': 'Nije završeno',
        'duration': 'Trajanje',
        'learning_resources': 'Resursi za učenje dostupni tokom pokušaja',
        # Days of the week
        'Monday': 'Ponedeljak',
        'Tuesday': 'Utorak',
        'Wednesday': 'Sreda',
        'Thursday': 'Četvrtak',
        'Friday': 'Petak',
        'Saturday': 'Subota',
        'Sunday': 'Nedelja',
        # Learner categories
        'one_shot_quick_quiz_completer': 'Jednopokušajni Brzi Završavač Kvizova',
        'incomplete_single_attempt_learner': 'Nepotpuni Jednopokušajni Učenik',
        'improving_multi_attempt_quiz_performer': 'Napredujući Višepokušajni Izvođač Kvizova',
        'consistent_multi_attempt_quiz_performer': 'Dosledni Višepokušajni Izvođač Kvizova',
        'high_effort_struggling_quiz_learner': 'Učenik koji se Muči sa Velikim Ulaganjem',
        'low_engagement_disengaged_quiz_learner': 'Neangažovani Učenik sa Niskom Uključenosti',
        'inconsistent_partial_quiz_performer': 'Nedosledan Delimični Izvođač Kvizova',
        'unclassified': 'Neklasifikovan',
        # Difficulty levels
        'Low': 'Nizak',
        'Medium': 'Srednji',
        'High': 'Visok',
        # Actions
        'autosaved': 'Automatsko čuvanje (autosaved)',
        'viewed': 'Pregled (viewed)',
        'uploaded': 'Otpremanje (uploaded)',
        'updated': 'Ažuriranje (updated)',
        'reviewed': 'Ponovni pregled (reviewed)',
        'replied': 'Odgovor (replied)',
        'started': 'Pokretanje (started)',
        'submitted': 'Podnošenje (submitted)',
        'removed': 'Uklanjanje (removed)',
        'created': 'Kreiranje (created)',
        'accepted': 'Prihvatanje (accepted)',
        'graded': 'Ocenjivanje (graded)',
    },
    'english': {
        'quiz_statistics': 'Statistics',
        'module_statistics': 'Statistics for Quiz Activities',
        'total_quizzes': 'Total Quizzes',
        'total_learners': 'Total Learners',
        'completion_rate': 'Overall Completion Rate',
        'avg_attempts': 'Average Attempts per Learner',
        'max_attempts': 'Maximum Attempts by a Single Learner',
        'multiple_attempts': 'Learners with Multiple Attempts',
        'peak_activity_hour': 'Peak Activity Hour',
        'peak_activity_day': 'Peak Activity Day',
        'action_distribution': 'Action Distribution',
        'attempt_distribution': 'Attempt Distribution',
        'attempt_s': 'attempt(s)',
        'learner_behavior': 'Learner Behavior & Performance',
        'grades': 'Grades',
        'cognitive': 'Cognitive',
        'communication': 'Communication',
        'creativity': 'Creativity',
        'critical_thinking': 'Critical Thinking',
        'collaboration': 'Collaboration',
        'learner_type_distribution': 'Learner Type Distribution',
        'engagement_metrics': 'Engagement Metrics',
        'avg_completion_per_user': 'Average Completion Rate per User',
        'avg_time_per_user': 'Average Time per User',
        'avg_actions_per_user': 'Average Actions per User',
        'decreasing_time': 'Learners with Decreasing Completion Time Across Attempts',
        'struggle_analysis': 'Quiz Difficulty Analysis Based on Learner Performance',
        'learners': 'learners',
        'learner_engagement_profile': 'Learner Engagement Profile',
        'learner_type': 'Learner Type',
        'total_attempts': 'Total Attempts',
        'completed_attempts': 'Completed Attempts',
        'total_time_spent': 'Total Time Spent',
        'avg_time_per_attempt': 'Average Time per Attempt',
        'improving_efficiency': 'Improving Efficiency / Reduced Time Across Attempts',
        'yes': 'Yes',
        'no': 'No',
        'action_frequency': 'Action Frequency',
        'attempt_details': 'Attempt Details',
        'start_attempt': 'Start',
        'end_attempt': 'End',
        'attempt': 'Attempt',
        'completed': 'Completed',
        'not_completed': 'Not Completed',
        'duration': 'Duration',
        'learning_resources': 'Learning Resources Accessed During the Attempt',
        
        # Days of the week
        'Monday': 'Monday',
        'Tuesday': 'Tuesday',
        'Wednesday': 'Wednesday',
        'Thursday': 'Thursday',
        'Friday': 'Friday',
        'Saturday': 'Saturday',
        'Sunday': 'Sunday',
        
        # Learner categories
        'one_shot_quick_quiz_completer': 'One-Shot Quick Quiz Completer',
        'incomplete_single_attempt_learner': 'Incomplete Single-Attempt Learner',
        'improving_multi_attempt_quiz_performer': 'Improving Multi-Attempt Quiz Performer',
        'consistent_multi_attempt_quiz_performer': 'Consistent Multi-Attempt Quiz Performer',
        'high_effort_struggling_quiz_learner': 'High-Effort Struggling Quiz Learner',
        'low_engagement_disengaged_quiz_learner': 'Low Engagement / Disengaged Quiz Learner',
        'inconsistent_partial_quiz_performer': 'Inconsistent Partial Quiz Performer',
        'unclassified': 'Unclassified',
        
        # Difficulty levels
        'Low': 'Low',
        'Medium': 'Medium',
        'High': 'High',
        
        # Actions
        'autosaved': 'Autosaved',
        'viewed': 'Viewed',
        'uploaded': 'Uploaded',
        'updated': 'Updated',
        'reviewed': 'Reviewed',
        'replied': 'Replied',
        'started': 'Started',
        'submitted': 'Submitted',
        'removed': 'Removed',
        'created': 'Created',
        'accepted': 'Accepted',
        'graded': 'Graded',
    }    
}

    
    
def identify_attempts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify individual quiz attempts for each user in the DataFrame.

    An attempt is defined by detecting 'started' actions in chronological order 
    per user. The function assigns an 'attempt_number' to each row, starting at 0 
    for the first attempt, incrementing by 1 on each new 'started' action.

    Parameters:
    -----------
    df : pd.DataFrame
        Input DataFrame containing user actions with at least the following columns:
        - 'username': identifier for each learner/user
        - 'action': action taken by the user (e.g., 'started')
        - 'action_time_unix': timestamp of the action in Unix time for sorting

    Returns:
    --------
    pd.DataFrame
        A copy of the input DataFrame with an added 'attempt_number' column indicating 
        the attempt index for each action. Attempt numbering starts at 0.
    """

    df_with_attempts = df.copy()
    df_with_attempts['attempt_number'] = 0
    
    for username in df['username'].unique():
        user_data = df[df['username'] == username].sort_values('action_time_unix')
        attempt_num = 0
        
        for idx, row in user_data.iterrows():
            if row['action'] == 'started':
                attempt_num += 1
            df_with_attempts.loc[idx, 'attempt_number'] = attempt_num - 1
    
    return df_with_attempts

def analyze_single_attempt(attempt_data: pd.DataFrame) -> dict | None:
    """
    Analyze a single quiz attempt by summarizing timing and action metrics.

    This function processes a DataFrame slice containing all actions for a single attempt,
    computes various statistics related to timing, actions performed, and completion status.

    Parameters:
    -----------
    attempt_data : pd.DataFrame
        DataFrame containing actions for a single quiz attempt with columns including:
        - 'action': the action performed (e.g., 'started', 'viewed', 'submitted')
        - 'action_time_readable': datetime of the action
        - 'action_time_unix': Unix timestamp of the action (used for sorting)

    Returns:
    --------
    dict or None
        A dictionary with the following keys if attempt_data is not empty:
        - 'duration': total time spent on the attempt (in secs)
        - 'total_actions': total number of actions performed in this attempt
        - 'action_counts': dict counting each action type during the attempt
        - 'avg_time_between_actions': average time in seconds between consecutive actions
        - 'max_gap': maximum time gap in seconds between any two actions
        - 'completed': boolean indicating if the attempt was completed (i.e., 'submitted' present)
        - 'action_sequence': string showing the sequence of actions joined by '->'
        - 'start_time': datetime of the first action in the attempt
        - 'end_time': datetime of the last action in the attempt

        Returns None if input DataFrame is empty.
    """

    if len(attempt_data) == 0:
        return None
    
    # Sort by time
    attempt_data = attempt_data.sort_values('action_time_unix')
    
    # Calculate attempt duration
    start_time = attempt_data['action_time_readable'].iloc[0]
    end_time = attempt_data['action_time_readable'].iloc[-1]
    duration = (end_time - start_time).total_seconds()
    
    # Count actions
    action_counts = attempt_data['action'].value_counts().to_dict()
    
    # Calculate time gaps
    time_diffs = attempt_data['action_time_readable'].diff().dt.total_seconds()
    avg_time_between_actions = time_diffs.mean() if len(time_diffs) > 1 else 0
    max_gap = time_diffs.max() if len(time_diffs) > 1 else 0
    
    # Check if completed
    completed = 'submitted' in attempt_data['action'].values
    
    # Get action sequence
    action_sequence = ' -> '.join(attempt_data['action'].tolist())
    
    return {
        'duration': duration,
        'total_actions': len(attempt_data),
        'action_counts': action_counts,
        'avg_time_between_actions': avg_time_between_actions,
        'max_gap': max_gap,
        'completed': completed,
        'action_sequence': action_sequence,
        'start_time': start_time,
        'end_time': end_time
    }

def analyze_quiz_statistics(df: pd.DataFrame) -> dict:
    """
    Analyze overall course statistics based on user actions and quiz attempts.

    This function aggregates key metrics such as user participation, attempt counts,
    completion rates, and temporal activity patterns from a DataFrame of quiz actions.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing quiz action logs with columns including:
        - 'username': identifier for each user
        - 'quiz_id': identifier for each quiz
        - 'action': type of action performed (e.g., 'started', 'submitted')
        - 'action_time_readable': datetime of the action
    
    Returns:
    --------
    dict
        Dictionary containing overall course statistics:
        - 'total_users': total number of unique users
        - 'total_quizzes': total number of unique quizzes
        - 'total_actions': total number of recorded actions
        - 'completion_rate': percentage of users who submitted at least one quiz
        - 'avg_attempts_per_user': average number of attempts per user
        - 'max_attempts_by_user': maximum number of attempts by any single user
        - 'users_with_multiple_attempts': count of users with more than one attempt
        - 'peak_activity_hour': hour of the day with the highest user activity
        - 'peak_activity_day': day of the week with the highest user activity
        - 'most_common_action': the most frequently performed action overall
        - 'action_distribution': pandas Series counting each action type
        - 'user_attempt_distribution': distribution of total attempts per user as a pandas Series
    """
    df_attempts = identify_attempts(df)
    
    # Basic course info
    total_users = df['username'].nunique()
    total_quizzes = df['quiz_id'].nunique()
    total_actions = len(df)
    
    # Attempt analysis
    user_attempt_counts = df_attempts.groupby('username')['attempt_number'].max().reset_index()
    user_attempt_counts['total_attempts'] = user_attempt_counts['attempt_number'] + 1
    
    # Completion rates
    completed_users = df[df['action'] == 'submitted']['username'].nunique()
    completion_rate = (completed_users / total_users) * 100
    
    # Time analysis
    df['hour'] = df['action_time_readable'].dt.hour
    df['day_of_week'] = df['action_time_readable'].dt.day_name()
    
    # Most active times
    peak_hour = df['hour'].mode().iloc[0] if not df['hour'].empty else None
    peak_day = f"{df['day_of_week'].mode().iloc[0]} ({df['action_time_readable'].iloc[0].date().isoformat()})" if not df['day_of_week'].empty else None
    
    # Action frequency
    action_distribution = df['action'].value_counts()
    
    return {
        'total_users': total_users,
        'total_quizzes': total_quizzes,
        'total_actions': total_actions,
        'completion_rate': completion_rate,
        'avg_attempts_per_user': user_attempt_counts['total_attempts'].mean(),
        'max_attempts_by_user': user_attempt_counts['total_attempts'].max(),
        'users_with_multiple_attempts': (user_attempt_counts['total_attempts'] > 1).sum(),
        'peak_activity_hour': peak_hour,
        'peak_activity_day': peak_day,
        'action_distribution': action_distribution,
        'user_attempt_distribution': user_attempt_counts['total_attempts'].value_counts().sort_index()
    }

def analyze_learner_characteristics(df: pd.DataFrame, pilot:str=None) -> dict:
    """
    Analyze individual learner characteristics across all quiz attempts.

    This function processes a DataFrame of quiz actions, identifies attempts per user,
    analyzes each attempt's details, and aggregates learner behavior and performance
    metrics across all attempts to generate a profile for each learner.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing quiz interaction logs with columns including:
        - 'username': identifier for each learner
        - 'action': action performed (e.g., 'started', 'submitted', 'viewed')
        - 'action_time_readable': datetime of each action
        - Other columns necessary for attempt identification and analysis
    pilot : str, optional
        Identifier used to retrieve the correct low/high threshold values for struggle analysis
        (used in `compute_histogram_bins` via `d_threshold[pilot]`).
            
    Returns:
    --------
    dict
        A dict where each element is a dictionary representing a learner's profile with keys:
        - 'total_attempts': total number of attempts made by the learner
        - 'completed_attempts': number of attempts completed (submitted)
        - 'total_time_spent': total time spent across all attempts
        - 'total_actions': total number of recorded actions
        - 'total_clicks': total number of clicks
        - 'avg_time_per_attempt': average duration per attempt (seoonds)
        - 'completion_rate': percentage of attempts completed
        - 'improving_over_attempts': boolean indicating if time spent per attempt is improving
        - 'consistent_completion': boolean indicating if completion behavior is consistent
        - 'struggle_score': composite score estimating learner struggle based on behavior
        - 'learner_type': categorical label classifying learner behavior
        - 'action_frequency': dictionary with counts of each action type performed
        - 'attempts_details': list of dictionaries with detailed analysis per attempt
    """
    df_attempts = identify_attempts(df)
    learner_profiles = {}
    
    for username in df['username'].unique():
        user_data = df_attempts[df_attempts['username'] == username]       
        # Basic info
        total_attempts = user_data['attempt_number'].max() + 1
        total_actions = len(user_data)
        total_clicks = len(user_data[user_data['action'] != "autosaved"])

        # Analyze each attempt
        attempts_analysis = []
        for attempt_num in range(total_attempts):
            attempt_data = user_data[user_data['attempt_number'] == attempt_num]
            attempt_analysis = analyze_single_attempt(attempt_data)
            if attempt_analysis:
                attempts_analysis.append(attempt_analysis)
        
        if not attempts_analysis:
            continue

        # Calculate overall metrics
        total_time_spent = sum([att['duration'] for att in attempts_analysis])
        completed_attempts = sum([1 for att in attempts_analysis if att['completed']])

        # Improvement analysis (if multiple attempts)
        is_time_improving = False
        consistent_completion = True
        if len(attempts_analysis) > 1:
            time_duration = [item['duration'] for item in attempts_analysis if item['completed']]
            if len(time_duration) > 1 and calculate_trent(np.array(time_duration)) < -5: is_time_improving = True
            
            # Check completion consistency
            completion_pattern = [att['completed'] for att in attempts_analysis]
            consistent_completion = all(completion_pattern) or completion_pattern[-1]
        
        # Behavioral patterns
        all_actions = user_data['action'].tolist()
        action_frequency = Counter(all_actions)
        
        # Struggle indicators
        total_views = action_frequency.get('viewed', 0)
        total_autosaves = action_frequency.get('autosaved', 0)
        avg_gap = np.mean([att['avg_time_between_actions'] for att in attempts_analysis if att['avg_time_between_actions'] > 0])
        
        struggle_score = (total_views / total_attempts * 0.3) + \
                        (total_autosaves / total_attempts * 0.2) + \
                        (min(avg_gap, 10) / 10 * 0.3) + \
                        ((total_attempts - 1) * 0.2)
        
        # Categorize learner
        learner_type = categorize_quiz_learner(total_attempts, pilot, struggle_score, completed_attempts, is_time_improving)
        
        learner_profiles[username] = {
            'total_attempts': total_attempts,
            'completed_attempts': completed_attempts,
            'total_time_spent': total_time_spent,
            'total_actions': total_actions,
            "total_clicks": total_clicks,
            'avg_time_per_attempt': total_time_spent / total_attempts,
            'completion_rate': (completed_attempts / total_attempts) * 100,
            'improving_over_attempts': is_time_improving,
            'consistent_completion': consistent_completion,
            'struggle_score': struggle_score,
            'learner_type': learner_type,
            'action_frequency': dict(action_frequency),
            'attempts_details': attempts_analysis
        }
    
    return learner_profiles

def categorize_quiz_learner(attempts, pilot, struggle_score, completed, is_time_improving):
    """
    Categorizes learners based on their quiz behavior using number of attempts, 
    completion rate, time-efficiency trends, and engagement level.

    Args:
        attempts (int): Total number of quiz attempts by the learner.
        pilot (str): Identifier for the learner group (used for threshold selection).
        total_time (float): Cumulative time spent on quizzes.
        struggle_score (float): Score indicating engagement or effort level.
        completed (int): Number of quizzes completed by the learner.
        is_time_improving (bool): Whether time spent per quiz is decreasing (indicating efficiency gain).

    Returns:
        str: A descriptive category label for the learner's quiz behavior.

    Categories:
        - "One-Shot Quick Quiz Completer":
            Completed the quiz in a single attempt.
        - "Incomplete Single Attempt Learner":
            Attempted once but did not complete the quiz.
        - "Improving Multi-Attempt Quiz Performer":
            Multiple attempts, high completion rate (≥80%), and improving time efficiency.
        - "Consistent Multi-Attempt Quiz Performer":
            Multiple attempts, high completion rate (≥80%), but no time improvement.
        - "High-Effort Struggling Quiz Learner":
            Multiple attempts, low completion rate (<40%), high struggle/effort.
        - "Low-Engagement Disengaged Quiz Learner":
            Multiple attempts, low completion rate (<40%), low or moderate struggle.
        - "Inconsistent Partial Quiz Performer":
            Moderate completion rate (40–79%), regardless of time improvement.
        - "Unclassified":
            Fallback category for edge cases or unexpected input.

    Notes:
        - `d_threshold` must be defined externally, containing per-pilot 'high' struggle thresholds.
        - Completion rate is calculated as `completed / attempts`.
    """
    completion_rate = completed / attempts if attempts > 0 else 0
    is_high_effort = struggle_score > d_threshold[pilot]['high']
    
    # Single attempt learners
    if attempts == 1:
        if completed == 1:
            return "one_shot_quick_quiz_completer"
        else:
            return "incomplete_single_attempt_learner"
    
    # Multi-attempt learners
    elif attempts > 1:
        # High completion rate (80%+)
        if completion_rate >= 0.8:
            if is_time_improving:
                return "improving_multi_attempt_quiz_performer"
            else:
                return "consistent_multi_attempt_quiz_performer"
        
        # Low/no completion rate
        elif completion_rate < 0.4:
            if is_high_effort:
                return "high_effort_struggling_quiz_learner"
            else:
                return "low_engagement_disengaged_quiz_learner"
        
        # Moderate completion rate (40-79%)
        else:
            return "inconsistent_partial_quiz_performer"
    else:
        return "unclassified"


def generate_quiz_statistics(df: pd.DataFrame, pilot: str = None, quiz_ids: list = None, module_id: int = None,
                             course_id:int=None, graph:Neo4jConnection=None, moodle_settings: dict=None, cursor: mysql.connector.cursor.MySQLCursor = None):
    """
    Generate detailed learner- and activity-level statistics for quiz-based learning interactions.

    This function analyzes learners’ behavior and quiz activity patterns using data from a log DataFrame.
    It incorporates resource interactions (e.g., pages, assignments) accessed during each quiz attempt,
    leveraging Moodle and Neo4j data sources. Results include per-learner profiles and aggregated activity metrics.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing quiz activity logs. Must include at least: 'quiz_id', 'action', 'user',
        'timestamp', and related metadata for attempt-level analysis.

    pilot : str, optional
        Identifier for the pilot/study context, used to select threshold values for struggle level classification.

    quiz_ids : list, optional
        List of quiz IDs to filter and analyze. Required for identifying quiz-specific interactions.

    module_id : int, optional
        Module identifier used for labeling in multi-quiz summaries.

    course_id : int, optional
        Course IDs used to filter learner-resource interactions within the appropriate context.

    graph : Neo4jConnection, optional
        Neo4j connection object used to retrieve resource-module relationships for activity mapping.

    moodle_settings : dict, optional
        Dictionary containing Moodle database connection parameters.

    cursor : mysql.connector.cursor.MySQLCursor, optional
        MySQL cursor used for querying Moodle logs to retrieve learner-resource interactions.

    Returns
    -------
    learner_stats : dict
        Dictionary where keys are learner usernames and values are formatted strings summarizing:
        - Learner type classification
        - Attempt and completion metrics
        - Time and engagement patterns
        - Action frequency
        - Learning resources accessed during each attempt

    learner_data : dict
        Dictionary with raw structured data (not formatted strings) per learner, including engagement metrics,
        struggle score, attempt breakdowns, and improvement trends.

    activity_stats : str
        A formatted string summarizing quiz-level insights including:
        - Number of quizzes and learners
        - Attempt and completion distribution
        - Action frequencies
        - Learner type breakdown
        - Performance metrics
        - Struggle level analysis

    activity_data : dict
        Raw metrics used to construct `activity_stats`, including counts, averages, and distributions.

    Raises
    ------
    Exception
        If no learners are found after filtering by `quiz_ids`.

    ValueError
        If the `pilot` parameter is not provided.

    Notes
    -----
    This function depends on:
    - `analyze_quiz_statistics(df)`
    - `analyze_learner_characteristics(df, pilot)`
    - `compute_histogram_bins(data, low, high)`
    - `retrieve_learner_interactions(...)`
    - `format_time(seconds, language)`

    It integrates Moodle logs with Neo4j-based activity mapping to provide a contextualized and detailed
    view of learner engagement with quizzes and related learning resources.
    """    
    # Sanity check
    if df[df['quiz_id'].isin(quiz_ids)].shape[0] == 0:
        raise Exception("No learners found participating the activity/activities")
    if not pilot:
        raise ValueError("No pilot is provided")
    # Set language & get the appropriate translation dictionary
    if pilot in ['IASIS', 'UPAT']:
        language = "greek" 
    elif pilot == 'EASD':
        language = 'serbian'
    elif pilot == 'KTU':
        language = 'english'        
    else:
        raise ValueError("Uknown pilot")
    t = translations[language]
     
    # Activity-level statistics
    activity_data = analyze_quiz_statistics(df=df[df['quiz_id'].isin(quiz_ids)])
    # Include grades
    activities_ids = [f"QUIZ:{idx}" for idx in quiz_ids]
    grades = graph.query(f"""
        MATCH (l:LEARNER)-[r]->(a:ACTIVITY) 
        WHERE 
            a.id IN {activities_ids} AND a.organization = '{pilot}' and l.organization = '{pilot}'
        RETURN 
            round(avg(r.Cognitive_grade), 1) AS Cognitive,
            round(avg(r.Communication_grade), 1) AS Communication,
            round(avg(r.Creativity_grade), 1) AS Creativity,
            round(avg(r.Critical_thinking_grade), 1) AS Critical_thinking,
            round(avg(r.Collaboration_grade), 1) AS Collaboration""")[0]
    if grades['Cognitive'] is not None:
        activity_data['Cognitive'] = grades['Cognitive']
    if grades['Communication'] is not None:
        activity_data['Communication'] = grades['Communication']
    if grades['Creativity'] is not None:
        activity_data['Creativity'] = grades['Creativity']
    if grades['Critical_thinking'] is not None:
        activity_data['Critical_thinking'] = grades['Critical_thinking']
    if grades['Collaboration'] is not None:
        activity_data['Collaboration'] = grades['Collaboration']   
    # Learner-level analysis
    learner_data = analyze_learner_characteristics(df=df[df['quiz_id'].isin(quiz_ids)], pilot=pilot)    
    # Include learners interactions
    if not module_id:    
        excluded_activies = [f"QUIZ:{id}" for id in quiz_ids]        
        for username, values in learner_data.items():
            for i, attempt in enumerate(values['attempts_details']):            
                attempt['interactions'] = retrieve_learner_interactions(username=username, start_time=attempt['start_time'], end_time=attempt['end_time'], course_id=course_id, excluded_activies=excluded_activies, graph=graph, moodle_settings=moodle_settings, cursor=cursor)
    
    
    # ----------------------------------------------------------------------------------
    
    # Activity statistics section
    if module_id:
        activity_stats = f"## {module_id} - {t['module_statistics'].format(module_id)}\n\n"
        activity_stats += f" - {t['total_quizzes']}: {activity_data['total_quizzes']}\n"        
    else:
        activity_stats = f"## QUIZ:{quiz_ids[0]} - {t['quiz_statistics'].format(quiz_ids[0])}\n\n"    

    activity_stats += f" - {t['total_learners']}: {activity_data['total_users']}\n"
    activity_stats += f" - {t['completion_rate']}: {activity_data['completion_rate']:.1f}%\n"     
    activity_stats += f" - {t['avg_attempts']}: {activity_data['avg_attempts_per_user']:.2f}\n"
    activity_stats += f" - {t['max_attempts']}: {activity_data['max_attempts_by_user']}\n"
    activity_stats += f" - {t['multiple_attempts']}: {activity_data['users_with_multiple_attempts']}\n"
    if not module_id:
        activity_stats += f" - {t['peak_activity_hour']}: {activity_data['peak_activity_hour']}:00\n"
        week_day, date = activity_data['peak_activity_day'].split(" ")
        activity_stats += f" - {t['peak_activity_day']}: {t[week_day]} {date}\n"

    activity_stats += f"\n**{t['action_distribution']}** ⚙️\n"
    for action, count in activity_data['action_distribution'].items():
        percentage = (count / activity_data['total_actions']) * 100
        activity_stats += f" - {t[action]}: {percentage:.1f}%\n"

    activity_stats += f"\n**{t['attempt_distribution']}** 🔄\n"
    for attempts, count in activity_data['user_attempt_distribution'].items():
        percentage = (count / activity_data['total_users']) * 100
        activity_stats += f"- {attempts} {t['attempt_s']}: {percentage:.1f}%\n"
     
        
    activity_stats += f"\n\n### {t['learner_behavior']}\n"
    
    # Grades
    if 'Cognitive' in activity_data or 'Communication' in activity_data or 'Creativity' in activity_data or 'Critical_thinking' in activity_data or 'Collaboration' in activity_data:
        activity_stats += f"**{t['grades']}** ⚙️\n"
    if 'Cognitive' in activity_data:
        activity_stats += f" - {t['cognitive']}: {activity_data['Cognitive']}/100\n"
    if 'Communication' in activity_data:
        activity_stats += f" - {t['communication']}: {activity_data['Communication']}/100\n"
    if 'Creativity' in activity_data:
        activity_stats += f" - {t['creativity']}: {activity_data['Creativity']}/100\n"
    if 'Critical_thinking' in activity_data:
        activity_stats += f" - {t['critical_thinking']}: {activity_data['Critical_thinking']}/100\n"
    if 'Collaboration' in activity_data:
        activity_stats += f" - {t['collaboration']}: {activity_data['Collaboration']}/100\n"
            
    # Learner type distribution
    total_users = len(learner_data)
    learner_type_counts = {}
    for _, values in learner_data.items():
        lt = values['learner_type']
        learner_type_counts[lt] = learner_type_counts.get(lt, 0) + 1

    activity_stats += f"\n**{t['learner_type_distribution']}** 🧠\n"
    for learner_type, count in learner_type_counts.items():
        percentage = (count / total_users) * 100
        activity_stats += f" - {t[learner_type]}: {percentage:.1f}%\n"

    # Engagement metrics
    avg_completion_rate = sum(values['completion_rate'] for _, values in learner_data.items()) / total_users
    avg_time_spent = sum(values['total_time_spent'] for _, values in learner_data.items()) / total_users
    avg_actions = sum(values['total_actions'] for _, values in learner_data.items()) / total_users
    users_improving = sum(1 for _, values in learner_data.items() if values['improving_over_attempts'])

    activity_stats += f"\n**{t['engagement_metrics']}** 📊\n"
    activity_stats += f" - {t['avg_completion_per_user']}: {avg_completion_rate:.1f}%\n"
    activity_stats += f" - {t['avg_time_per_user']}: {format_time(avg_time_spent, language)}\n"
    activity_stats += f" - {t['avg_actions_per_user']}: {avg_actions:.1f}\n"
    activity_stats += f" - {t['decreasing_time']}: {(users_improving / total_users)*100:.1f}%\n"

    # Struggle analysis
    activity_stats += f"\n**{t['struggle_analysis']}** 🎯\n"
    struggle = compute_histogram_bins(data=[values['struggle_score'] for _, values in learner_data.items()], low=d_threshold[pilot]['low'], high=d_threshold[pilot]['high'])
    for key, value in struggle.items():
        activity_stats += f" - {t[key]}: {value:.1f}% {t['learners']}\n"

    # ----------------------------------------------------------------------------------

    # Learner statistics section
    learner_stats = dict()   
    for username, values in learner_data.items():
        learner_stats[username] = f"**{t['learner_engagement_profile']}** 🧑‍🎓\n"
        learner_stats[username] += f" - {t['learner_type']}: {t[values['learner_type']]}\n"
        learner_stats[username] += f" - {t['total_attempts']}: {values['total_attempts']}\n"
        learner_stats[username] += f" - {t['completed_attempts']}: {values['completed_attempts']}\n"
        learner_stats[username] += f" - {t['completion_rate']}: {values['completion_rate']:.1f}%\n"
        learner_stats[username] += f" - {t['total_time_spent']}: {format_time(values['total_time_spent'], language)}\n"
        
        if values['total_attempts'] > 1:
            learner_stats[username] += f" - ⏱️ {t['avg_time_per_attempt']}: {format_time(values['avg_time_per_attempt'], language)}\n"
            improving_text = t['yes'] if values['improving_over_attempts'] else t['no']
            learner_stats[username] += f" - 📈{t['improving_efficiency']}: {improving_text}\n"
            
        learner_stats[username] += f"\n**{t['action_frequency']}** 📊\n"
        for action, count in values['action_frequency'].items():
            learner_stats[username] += f" - {t[action]}: {count}\n"
        
        if not module_id:
            learner_stats[username] += f"\n**{t['attempt_details']}** 📝\n"
            for i, attempt in enumerate(values['attempts_details']):
                completed_text = f"{t['completed']} ✅" if attempt['completed'] else f"{t['not_completed']} ❌"
                learner_stats[username] += f" - {t['attempt']} {i+1}  ({completed_text})\n"
                if attempt['duration'] > 0:
                    learner_stats[username] += f"    * ⏰ {t['start_attempt']}: {attempt['start_time'].strftime('%d-%m-%Y %H:%M:%S')}\n"
                    learner_stats[username] += f"    * 🏁 {t['end_attempt']}: {attempt['end_time'].strftime('%d-%m-%Y %H:%M:%S')}\n"                    
                learner_stats[username] += f"    * ⏱️ {t['duration']}: {format_time(attempt['duration'], language)}\n"
                
                # Include user interactions
                if attempt['interactions']:
                    learner_stats[username] += f"    * 📚 {t['learning_resources']}: {', '.join(attempt['interactions'])}\n"
                
    return learner_stats, learner_data, activity_stats, activity_data