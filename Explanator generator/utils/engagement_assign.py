import pandas as pd
import numpy as np
import mysql.connector
from utils.neo4j_connection import Neo4jConnection
from datetime import datetime, timedelta
from collections import Counter
from utils.utils import format_time, calculate_trent
from utils.engagement_utils import retrieve_learner_interactions

d_threshold = {'UPAT': {'low': 2.2, 'high': 3.2},
               'IASIS': {'low': 2, 'high': 3},
               'EASD': {'low': 0.6, 'high': 2.1},
               'KTU': {'low': 2.2, 'high': 3.2} # TODO
               }

# Translation dictionaries
translations = {
    'greek': {
        'statistics_about_assignment': 'Στατιστικά για τις Δραστηριότητες Εργασίας',
        'statistics': 'Στατιστικά',
        'total_assignments': 'Συνολικές Εργασίες',
        'total_learners': 'Σύνολο Μαθητών',
        'overall_submission_rate': 'Συνολικό Ποσοστό Υποβολής',
        'average_sessions_per_learner': 'Μέσος Όρος Συνεδριών ανά Μαθητή',
        'maximum_sessions_by_single_learner': 'Μέγιστες Συνεδρίες από Έναν Μαθητή',
        'learners_with_multiple_sessions': 'Μαθητές με Πολλαπλές Συνεδρίες',
        'peak_activity_hour': 'Ώρα Αιχμής Δραστηριότητας',
        'peak_activity_day': 'Ημέρα Αιχμής Δραστηριότητας',
        'action_distribution': 'Κατανομή Ενεργειών',
        'session_distribution': 'Κατανομή Συνεδριών',
        'sessions': 'συνεδρία(-ες)',
        'learner_behavior_performance': 'Συμπεριφορά και Απόδοση Μαθητών',
        'grades': 'Βαθμολογίες',
        'cognitive': 'Γνωστικό',
        'communication': 'Επικοινωνία',
        'creativity': 'Δημιουργικότητα',
        'critical_thinking': 'Κριτική Σκέψη',
        'collaboration': 'Συνεργασία',
        'learner_type_distribution': 'Κατανομή Τύπων Μαθητών',
        'engagement_metrics': 'Μετρήσεις Συμμετοχής',
        'average_submission_rate_per_learner': 'Μέσος Όρος Ποσοστού Υποβολής ανά Μαθητή',
        'average_time_spent_per_learner': 'Μέσος Όρος Χρόνου ανά Μαθητή',
        'learners_showing_efficiency_improvement': 'Μαθητές που Δείχνουν Βελτίωση Αποδοτικότητας (μείωση διάρκειας συνεδρίας)',
        'learner_engagement_profile': 'Προφίλ Συμμετοχής Μαθητή',
        'learner_type': 'Τύπος Μαθητή',
        'total_sessions': 'Συνολικές Συνεδρίες',
        'submitted_sessions': 'Υποβληθείσες Συνεδρίες',
        'submission_rate': 'Ποσοστό Υποβολής',
        'total_time_spent': 'Συνολικός Χρόνος',
        'average_time_per_session': 'Μέσος Όρος Χρόνου ανά Συνεδρία',
        'improving_efficiency': 'Βελτίωση Αποδοτικότητας/Μείωση διάρκειας συνεδρίας',
        'action_frequency': 'Συχνότητα Ενεργειών',
        'session_details': 'Λεπτομέρειες Συνεδρίας',
        'start_session': 'Έναρξη συνεδρίας',
        'end_session': 'Τερματισμός συνεδρίας',        
        'session': 'Συνεδρία',
        'submitted_assignment': 'Υποβλήθηκε',     
        'not_submitted_assignment': 'Δεν Υποβλήθηκε',
        'duration': 'Διάρκεια',
        'associated_learning_resources': 'Πόροι μάθησης που έγιναν προσπελάσιμοι κατά τη διάρκεια της προσπάθειας', # 'Συναφείς μαθησιακοί πόροι που προσπελάστηκαν κατά τη διάρκεια της προσπάθειας',
        'yes': 'Ναι',
        'no': 'Όχι',
        # Learner classification
        'high_effort_single_session': 'Μαθητής Μίας Συνεδρίας με Υψηλή Προσπάθεια',
        'quick_single_session_completer': 'Γρήγορος Ολοκληρωτής Μίας Συνεδρίας',
        'engaged_single_session_non_completer': 'Ενεργός Μαθητής Μίας Συνεδρίας Χωρίς Ολοκλήρωση',
        'minimal_single_session_participant': 'Μινιμαλιστής Συμμετέχων Μίας Συνεδρίας',
        'high_growth_persistent_learner': 'Επίμονος Μαθητής με Υψηλή Ανάπτυξη',
        'steady_improver': 'Σταθερός Βελτιωτής',
        'high_effort_consistent_performer': 'Συνεπής Εκτελεστής με Υψηλή Προσπάθεια',
        'efficient_consistent_performer': 'Αποδοτικός Συνεπής Εκτελεστής',
        'developing_partial_participant': 'Αναπτυσσόμενος Μερικός Συμμετέχων',
        'struggling_partial_participant': 'Αγωνιζόμενος Μερικός Συμμετέχων',
        'inconsistent_participant': 'Ασυνεπής Συμμετέχων',
        'high_effort_minimal_submitter': 'Μινιμαλιστής Υποβάλλων με Υψηλή Προσπάθεια',
        'sporadic_minimal_submitter': 'Σποραδικός Μινιμαλιστής Υποβάλλων',
        'engaged_observer': 'Ενεργός Παρατηρητής',
        'passive_observer': 'Παθητικός Παρατηρητής',
        'disengaged_participant': 'Αποσυνδεδεμένος Συμμετέχων',
        'unclassified': 'Μη Κατηγοριοποιημένος',     
        # Days of the week
        'Monday': 'Δευτέρα',
        'Tuesday': 'Τρίτη',
        'Wednesday': 'Τετάρτη',
        'Thursday': 'Πέμπτη',
        'Friday': 'Παρασκευή',
        'Saturday': 'Σάββατο',
        'Sunday': 'Κυριακή',
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
        'graded': 'Βαθμολόγηση (graded)'
},
    'serbian': {
        'statistics_about_assignment': 'Statistika o aktivnostima zadataka',
        'statistics': 'Statistika',
        'total_assignments': 'Ukupno zadataka',
        'total_learners': 'Ukupno učenika',
        'overall_submission_rate': 'Ukupna stopa predaje',
        'average_sessions_per_learner': 'Prosečno sesija po učeniku',
        'maximum_sessions_by_single_learner': 'Maksimalno sesija od jednog učenika',
        'learners_with_multiple_sessions': 'Učenici sa više sesija',
        'peak_activity_hour': 'Vreme najveće aktivnosti',
        'peak_activity_day': 'Dan najveće aktivnosti',
        'action_distribution': 'Distribucija akcija',
        'session_distribution': 'Distribucija sesija',
        'sessions': 'sesija(e)',
        'learner_behavior_performance': 'Ponašanje i performanse učenika',
        'grades': 'Ocene',
        'cognitive': 'Kognitivno',
        'communication': 'Komunikacija',
        'creativity': 'Kreativnost',
        'critical_thinking': 'Kritičko mišljenje',
        'collaboration': 'Saradnja',
        'learner_type_distribution': 'Distribucija tipova učenika',
        'engagement_metrics': 'Mere angažovanja',
        'average_submission_rate_per_learner': 'Prosečna stopa predaje po učeniku',
        'average_time_spent_per_learner': 'Prosečno vreme po učeniku',
        'learners_showing_efficiency_improvement': 'Učenici koji pokazuju poboljšanje efikasnosti (smanjenje trajanja sesije)',
        'learner_engagement_profile': 'Profil angažovanja učenika',
        'learner_type': 'Tip učenika',
        'total_sessions': 'Ukupno sesija',
        'submitted_sessions': 'Predate sesije',
        'submission_rate': 'Stopa predaje',
        'total_time_spent': 'Ukupno vreme',
        'average_time_per_session': 'Prosečno vreme po sesiji',
        'improving_efficiency': 'Poboljšanje efikasnosti/Smanjenje trajanja sesije',
        'action_frequency': 'Frekvencija akcija',
        'session_details': 'Detalji sesije',
        'start_session': 'Početak sesije',
        'end_session': 'Završetak sesije',        
        'session': 'Sesija',
        'submitted_assignment': 'Predato',
        'not_submitted_assignment': 'Nije predato',
        'duration': 'Trajanje',
        'associated_learning_resources': 'Resursi za učenje dostupni tokom pokušaja', # 'Povezani resursi za učenje kojima se pristupilo tokom pokušaja',
        'yes': 'Da',
        'no': 'Ne',
        # Learner classification
        'high_effort_single_session': 'Učenik jedne sesije sa velikim naporom',
        'quick_single_session_completer': 'Brzi završetak jedne sesije',
        'engaged_single_session_non_completer': 'Angažovani učenik jedne sesije bez završetka',
        'minimal_single_session_participant': 'Minimalni učesnik jedne sesije',
        'high_growth_persistent_learner': 'Uporan učenik sa velikim rastom',
        'steady_improver': 'Stabilni napredovalac',
        'high_effort_consistent_performer': 'Dosledni izvršilac sa velikim naporom',
        'efficient_consistent_performer': 'Efikasni dosledni izvršilac',
        'developing_partial_participant': 'Učesnik u razvoju sa parcijalnim učešćem',
        'struggling_partial_participant': 'Učesnik u borbi sa parcijalnim učešćem',
        'inconsistent_participant': 'Nedosledno učešće',
        'high_effort_minimal_submitter': 'Minimalni pošaljilac sa velikim naporom',
        'sporadic_minimal_submitter': 'Sporadični minimalni pošaljilac',
        'engaged_observer': 'Angažovani posmatrač',
        'passive_observer': 'Pasivni posmatrač',
        'disengaged_participant': 'Nezainteresovani učesnik',
        'unclassified': 'Neklasifikovano',
        # Days of the week
        'Monday': 'Ponedeljak',
        'Tuesday': 'Utorak',
        'Wednesday': 'Sreda',
        'Thursday': 'Četvrtak',
        'Friday': 'Petak',
        'Saturday': 'Subota',
        'Sunday': 'Nedelja',    
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
        'statistics_about_assignment': 'Statistics for Assignment Activities',
        'statistics': 'Statistics',
        'total_assignments': 'Total Assignments',
        'total_learners': 'Total Learners',
        'overall_submission_rate': 'Overall Submission Rate',
        'average_sessions_per_learner': 'Average Sessions per Learner',
        'maximum_sessions_by_single_learner': 'Maximum Sessions by a Single Learner',
        'learners_with_multiple_sessions': 'Learners with Multiple Sessions',
        'peak_activity_hour': 'Peak Activity Hour',
        'peak_activity_day': 'Peak Activity Day',
        'action_distribution': 'Action Distribution',
        'session_distribution': 'Session Distribution',
        'sessions': 'session(s)',
        'learner_behavior_performance': 'Learner Behavior and Performance',
        'grades': 'Grades',
        'cognitive': 'Cognitive',
        'communication': 'Communication',
        'creativity': 'Creativity',
        'critical_thinking': 'Critical Thinking',
        'collaboration': 'Collaboration',
        'learner_type_distribution': 'Learner Type Distribution',
        'engagement_metrics': 'Engagement Metrics',
        'average_submission_rate_per_learner': 'Average Submission Rate per Learner',
        'average_time_spent_per_learner': 'Average Time Spent per Learner',
        'learners_showing_efficiency_improvement': 'Learners Showing Efficiency Improvement (Reduced Session Duration)',
        'learner_engagement_profile': 'Learner Engagement Profile',
        'learner_type': 'Learner Type',
        'total_sessions': 'Total Sessions',
        'submitted_sessions': 'Submitted Sessions',
        'submission_rate': 'Submission Rate',
        'total_time_spent': 'Total Time Spent',
        'average_time_per_session': 'Average Time per Session',
        'improving_efficiency': 'Improving Efficiency / Reducing Session Duration',
        'action_frequency': 'Action Frequency',
        'session_details': 'Session Details',
        'start_session': 'Start Session',
        'end_session': 'End Session',
        'session': 'Session',
        'submitted_assignment': 'Submitted',
        'not_submitted_assignment': 'Not Submitted',
        'duration': 'Duration',
        'associated_learning_resources': 'Learning Resources Accessed During the Attempt',
        'yes': 'Yes',
        'no': 'No',

        # Learner classification
        'high_effort_single_session': 'High-Effort Single-Session Learner',
        'quick_single_session_completer': 'Quick Single-Session Completer',
        'engaged_single_session_non_completer': 'Engaged Single-Session Non-Completer',
        'minimal_single_session_participant': 'Minimal Single-Session Participant',
        'high_growth_persistent_learner': 'High-Growth Persistent Learner',
        'steady_improver': 'Steady Improver',
        'high_effort_consistent_performer': 'High-Effort Consistent Performer',
        'efficient_consistent_performer': 'Efficient Consistent Performer',
        'developing_partial_participant': 'Developing Partial Participant',
        'struggling_partial_participant': 'Struggling Partial Participant',
        'inconsistent_participant': 'Inconsistent Participant',
        'high_effort_minimal_submitter': 'High-Effort Minimal Submitter',
        'sporadic_minimal_submitter': 'Sporadic Minimal Submitter',
        'engaged_observer': 'Engaged Observer',
        'passive_observer': 'Passive Observer',
        'disengaged_participant': 'Disengaged Participant',
        'unclassified': 'Unclassified',

        # Days of the week
        'Monday': 'Monday',
        'Tuesday': 'Tuesday',
        'Wednesday': 'Wednesday',
        'Thursday': 'Thursday',
        'Friday': 'Friday',
        'Saturday': 'Saturday',
        'Sunday': 'Sunday',

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
    
def identify_submission_sessions(df:pd.DataFrame) -> pd.DataFrame:
    """
    Assigns session numbers to user actions based on inactivity gaps.

    This function analyzes a DataFrame of user activity logs and assigns 
    a session number to each row, identifying distinct user sessions 
    based on a 30-minute inactivity threshold.

    A new session is considered to start if either:
    - It's the user's first recorded action.
    - More than 30 minutes (1800 seconds) have passed since their last action.

    Parameters:
    ----------
    df : pandas.DataFrame
        A DataFrame containing at least the following columns:
        - 'username': identifier for each user.
        - 'action_time_unix': timestamp of the action in UNIX time (seconds).

    Returns:
    -------
    pandas.DataFrame
        A copy of the input DataFrame with an added 'session_number' column,
        where each number denotes the session group for that user's action.
    """
    df_with_sessions = df.copy()
    df_with_sessions['session_number'] = 0
    
    for username in df['username'].unique():
        user_data = df[df['username'] == username].sort_values('action_time_unix')
        session_num = 1
        last_time = None
        
        for idx, row in user_data.iterrows():
            # Start new session if more than 30 minutes gap or first action
            if last_time is None or (row['action_time_unix'] - last_time) > 1800:  # 30 minutes
                if last_time is not None:
                    session_num += 1
            df_with_sessions.loc[idx, 'session_number'] = session_num
            last_time = row['action_time_unix']
    
    return df_with_sessions

def analyze_single_session(session_data:pd.DataFrame) -> dict:
    """
    Analyzes a single user assignment session and extracts key metrics.

    This function takes a subset of user activity data corresponding to a 
    single session and computes various analytics, including duration, 
    action statistics, time gaps, and submission status.

    Parameters:
    ----------
    session_data : pandas.DataFrame
        A DataFrame containing action logs for a single session. Must include:
        - 'action_time_readable': datetime column of action timestamps.
        - 'action_time_unix': UNIX timestamp column (for sorting, optional).
        - 'action': string column describing the type of action (e.g., 'viewed', 'submitted').

    Returns:
    -------
    dict or None
        A dictionary containing the following keys:
        - 'duration': Total duration of the session in seconds.
        - 'total_actions': Total number of actions in the session.
        - 'action_counts': Dictionary of action types and their frequencies.
        - 'avg_time_between_actions': Average time (in seconds) between actions.
        - 'max_gap': Maximum time gap (in seconds) between any two actions.
        - 'submitted': Boolean indicating if a 'submitted' action occurred.
        - 'action_sequence': String representation of the ordered action sequence.
        - 'start_time': Datetime of the first action.
        - 'end_time': Datetime of the last action.

        Returns None if the session_data is empty.
    """

    if len(session_data) == 0:
        return None
    
    # Sort by time
    session_data = session_data.sort_values('action_time_unix')
    
    # Calculate session duration
    start_time = session_data['action_time_readable'].iloc[0]
    end_time = session_data['action_time_readable'].iloc[-1]
    duration = (end_time - start_time).total_seconds()
    
    # Count actions
    action_counts = session_data['action'].value_counts().to_dict()
    
    # Calculate time gaps
    time_diffs = session_data['action_time_readable'].diff().dt.total_seconds()
    avg_time_between_actions = time_diffs.mean() if len(time_diffs) > 1 else 0
    max_gap = time_diffs.max() if len(time_diffs) > 1 else 0
    
    # Check if submitted
    submitted = 'submitted' in session_data['action'].values
    
    # Get action sequence
    action_sequence = ' -> '.join(session_data['action'].tolist())
    
    return {
        'duration': duration,
        'total_actions': len(session_data),
        'action_counts': action_counts,
        'avg_time_between_actions': avg_time_between_actions,
        'max_gap': max_gap,
        'submitted': submitted,
        'action_sequence': action_sequence,
        'start_time': start_time,
        'end_time': end_time
    }



def analyze_assignment_statistics(df:pd.DataFrame) -> dict:
    """
    Computes summary statistics for assignment activity across an entire course.

    This function analyzes user interaction data related to course assignments, 
    identifying patterns such as session frequency, submission rates, and peak activity times. 
    It also provides high-level metrics on actions and engagement levels.

    Parameters:
    ----------
    df : pandas.DataFrame
        A DataFrame of user activity logs with at least the following columns:
        - 'username': user identifier.
        - 'assign_id': assignment identifier.
        - 'action': type of activity (e.g., 'viewed', 'submitted').
        - 'action_time_readable': timestamp of the action as a datetime object.
        - 'action_time_unix': timestamp of the action in UNIX time (used for session detection).

    Returns:
    -------
    dict
        A dictionary containing various course-wide statistics:
        - 'total_users': Number of unique users.
        - 'total_assignments': Number of unique assignments.
        - 'total_actions': Total number of recorded actions.
        - 'submission_rate': Percentage of users who submitted at least one assignment.
        - 'avg_sessions_per_user': Average number of sessions per user.
        - 'max_sessions_by_user': Maximum sessions recorded for a single user.
        - 'users_with_multiple_sessions': Number of users with more than one session.
        - 'peak_activity_hour': Hour of the day with the most activity.
        - 'peak_activity_day': Day of the week with the most activity.
        - 'most_common_action': Most frequently occurring action type.
        - 'action_distribution': pandas Series of action frequencies.
        - 'user_session_distribution': Series showing how many users had each session count.
    """

    df_sessions = identify_submission_sessions(df)
    
    # Basic course info
    total_users = df['username'].nunique()
    total_assignments = df['assign_id'].nunique()
    total_actions = len(df)
    
    # Session analysis
    user_session_counts = df_sessions.groupby('username')['session_number'].max().reset_index()
    user_session_counts['total_sessions'] = user_session_counts['session_number']
    
    # Submission rates
    submitted_users = df[df['action'] == 'submitted']['username'].nunique()
    submission_rate = (submitted_users / total_users) * 100
    
    # Time analysis
    df['hour'] = df['action_time_readable'].dt.hour
    df['day_of_week'] = df['action_time_readable'].dt.day_name()
    
    # Most active times
    peak_hour = df['hour'].mode().iloc[0] if not df['hour'].empty else None
    peak_day = f"{df['day_of_week'].mode().iloc[0]} ({df['action_time_readable'].iloc[0].date().isoformat()})" if not df['day_of_week'].empty else None

    # Action frequency
    action_distribution = df['action'].value_counts()
    most_common_action = action_distribution.index[0] if not action_distribution.empty else None
    
    return {
        'total_users': total_users,
        'total_assignments': total_assignments,
        'total_actions': total_actions,
        'submission_rate': submission_rate,
        'avg_sessions_per_user': user_session_counts['total_sessions'].mean(),
        'max_sessions_by_user': user_session_counts['total_sessions'].max(),
        'users_with_multiple_sessions': (user_session_counts['total_sessions'] > 1).sum(),
        'peak_activity_hour': peak_hour,
        'peak_activity_day': peak_day,
        'most_common_action': most_common_action,
        'action_distribution': action_distribution,
        'user_session_distribution': user_session_counts['total_sessions'].value_counts().sort_index()
    }

def analyze_learner_characteristics(df:pd.DataFrame, pilot:str=None) -> dict:
    """
    Analyzes individual Learner behavior across all assignment sessions to identify 
    engagement patterns, efficiency, and potential academic struggle.

    This function processes assignment activity logs per Learner, performs session-level 
    analysis, computes overall metrics, evaluates behavioral indicators, and assigns a 
    categorized Learner type using predefined rules.

    Parameters:
    ----------
    df : pandas.DataFrame
        A DataFrame of Learner activity logs containing the following columns:
        - 'username': Identifier for each Learner.
        - 'assign_id': Assignment identifier.
        - 'action': Action type (e.g., 'viewed', 'uploaded', 'submitted').
        - 'action_time_readable': Datetime of the action.
        - 'action_time_unix': Corresponding UNIX timestamp.
    pilot : str, optional
        Identifier used to retrieve the correct low/high threshold values for struggle analysis
        (used in `compute_histogram_bins` via `d_threshold[pilot]`).
        
    Returns:
    -------
        A dict where each element is a dictionary representing a learner's profile with keys:
        - 'username': Learner identifier.
        - 'total_sessions': Number of sessions recorded.
        - 'submitted_sessions': Count of sessions that included submission.
        - 'total_time_spent': Cumulative session duration in seconds.
        - 'total_actions': Number of recorded actions.
        - 'total_clicks': total number of clicks        
        - 'avg_time_per_session': Average session duration.
        - 'submission_rate': Percentage of sessions that ended in submission.
        - 'improving_efficiency': Boolean indicating if session duration decreased significantly.
        - 'consistent_work_pattern': Boolean indicating low variation in session duration.
        - 'engagement_score': Composite score based on views, downloads, uploads, and time spent.
        - 'struggle_score': Heuristic score indicating signs of struggle or at-risk behavior.
        - 'learner_type': Categorized label based on overall behavioral profile.
        - 'action_frequency': Dictionary of action types and their counts.
        - 'sessions_details': List of detailed session-level dictionaries (from analyze_single_session).
    """

    df_sessions = identify_submission_sessions(df)
    learner_profiles = dict()
    
    for username in df['username'].unique():
        user_data = df_sessions[df_sessions['username'] == username]
        
        # Basic info
        total_sessions = user_data['session_number'].max()
        total_actions = len(user_data)
        total_clicks = len(user_data[user_data['action'] != "autosaved"])
        
        # Analyze each session
        sessions_analysis = []
        for session_num in range(1, total_sessions + 1):
            session_data = user_data[user_data['session_number'] == session_num]
            session_analysis = analyze_single_session(session_data)
            if session_analysis:
                sessions_analysis.append(session_analysis)
        
        if not sessions_analysis:
            continue
            
        # Calculate overall metrics
        total_time_spent = sum([sess['duration'] for sess in sessions_analysis])
        submitted_sessions = sum([1 for sess in sessions_analysis if sess['submitted']])
        
        # Progress analysis (if multiple sessions)
        is_time_improving = False
        consistent_work_pattern = True
        if len(sessions_analysis) > 1:
            # Check if time per session decreased (more efficient)
            time_duration = [item['duration'] for item in sessions_analysis if item['submitted']]
            if len(time_duration) > 1 and calculate_trent(np.array(time_duration)) < 0: 
                is_time_improving = True
            
            # Check work pattern consistency
            session_durations = [sess['duration'] for sess in sessions_analysis]
            consistent_work_pattern = np.std(session_durations) < np.mean(session_durations) * 0.5
        
        # Behavioral patterns
        all_actions = user_data['action'].tolist()
        action_frequency = Counter(all_actions)
        
        # Engagement indicators
        total_views = action_frequency.get('viewed', 0)
        total_downloads = action_frequency.get('downloaded', 0)
        total_uploads = action_frequency.get('uploaded', 0)
        avg_gap = np.mean([sess['avg_time_between_actions'] for sess in sessions_analysis if sess['avg_time_between_actions'] > 0])
        
        # Calculate engagement score
        engagement_score = (total_views / total_sessions * 0.2) + \
                          (total_downloads / total_sessions * 0.2) + \
                          (total_uploads / total_sessions * 0.3) + \
                          (min(total_time_spent, 120) / 120 * 0.3) # Cap at 2 hours

        # NEW: Calculate struggle/risk score (adapted from quiz analysis)
        # Higher score indicates more risk/struggle
        struggle_score = 0
        
        # Multiple sessions with no submissions increase risk
        if total_sessions > 1 and submitted_sessions == 0:
            struggle_score += 3
        
        # Low submission rate increases risk
        submission_rate = (submitted_sessions / total_sessions) * 100 if total_sessions > 0 else 0
        if submission_rate < 30:
            struggle_score += 2
        elif submission_rate < 60:
            struggle_score += 1
        
        # Excessive viewing without action indicates confusion
        if total_views > total_sessions * 3:
            struggle_score += 1
        
        # Very long sessions or very short sessions can indicate issues
        avg_session_duration = total_time_spent / total_sessions if total_sessions > 0 else 0
        if avg_session_duration > 90:  # More than 1.5 hours per session
            struggle_score += 1
        elif avg_session_duration < 5 and submitted_sessions > 0:  # Very quick submissions
            struggle_score += 0.5
        
        # Large gaps between actions indicate confusion or distraction
        if avg_gap > 600:  # More than 10 min average between actions
            struggle_score += 1
        
        # Low engagement with high session count
        if total_sessions > 2 and engagement_score < 1:
            struggle_score += 2
        
        # Categorize Learner
        learner_type = categorize_assignment_learner(sessions=total_sessions, pilot=pilot,
                                                     struggle_score=struggle_score, 
                                                   submitted=submitted_sessions, improving=is_time_improving)

        
        learner_profiles[username] = {
            'total_sessions': total_sessions,
            'submitted_sessions': submitted_sessions,
            'total_time_spent': total_time_spent,
            'total_actions': total_actions,
            "total_clicks": total_clicks,            
            'avg_time_per_session': total_time_spent / total_sessions if total_sessions > 0 else 0,
            'submission_rate': submission_rate,
            'improving_efficiency': is_time_improving,
            'consistent_work_pattern': consistent_work_pattern,
            'engagement_score': engagement_score,
            'struggle_score': struggle_score, 
            'learner_type': learner_type,
            'action_frequency': dict(action_frequency),
            'sessions_details': sessions_analysis
        }
    
    return learner_profiles

def categorize_assignment_learner(sessions, pilot, submitted, improving, struggle_score):
    """
    Categorizes learners based on participation, submission behavior, improvement trend,
    and struggle score using Moodle assignment data.

    Args:
        sessions (int): Number of sessions the learner engaged with.
        pilot (str): Identifier for the pilot group (used to reference appropriate thresholds).
        submitted (int): Number of assignments submitted.
        improving (bool): Whether the learner shows performance improvement.
        struggle_score (float): Metric indicating engagement/effort level.

    Returns:
        str: A descriptive category label representing learner behavior.

    Categories:
        - "High-Effort Single Session Learner":
            Submitted in one session with high struggle/effort.
        - "Quick Single Session Completer":
            Submitted in one session with low struggle.
        - "Engaged Single Session Non-Completer":
            Did not submit, but showed moderate struggle/engagement.
        - "Minimal Single Session Participant":
            No submission and low struggle in one session.
        - "High-Growth Persistent Learner":
            Multi-session participant, high submission rate, shows improvement, high effort.
        - "Steady Improver":
            Multi-session, high submission rate, improving, moderate effort.
        - "High-Effort Consistent Performer":
            Multi-session, high submission rate, not improving, but high effort.
        - "Efficient Consistent Performer":
            Multi-session, high submission rate, not improving, low/moderate effort.
        - "Developing Partial Participant":
            Submitted in 20–80% of sessions, showing improvement.
        - "Struggling Partial Participant":
            Submitted in 20–80% of sessions, no improvement, high effort.
        - "Inconsistent Participant":
            Submitted in 20–80% of sessions, no improvement, low/moderate effort.
        - "High-Effort Minimal Submitter":
            Submitted in <20% of sessions, high struggle.
        - "Sporadic Minimal Submitter":
            Submitted in <20% of sessions, low/moderate struggle.
        - "Engaged Observer":
            No submission, but high struggle/engagement.
        - "Passive Observer":
            No submission, moderate struggle.
        - "Disengaged Participant":
            No submission, low struggle.
        - "Unclassified":
            Fallback category for unhandled edge cases.
    """
    # Handle single session learners
    if sessions == 1:
        if submitted == 1:
            if struggle_score > d_threshold[pilot]['high']:
                return "high_effort_single_session"
            else:
                return "quick_single_session_completer"
        else:
            if struggle_score > d_threshold[pilot]['low']:
                return "engaged_single_session_non_completer"
            else:
                return "minimal_single_session_participant"
    
    # Handle multi-session learners
    elif sessions > 1:
        submission_rate = submitted / sessions
        
        # High submission rate (80%+)
        if submission_rate >= 0.8:
            if improving:
                if struggle_score > d_threshold[pilot]['high']:
                    return "high_growth_persistent_learner"
                else:
                    return "steady_improver"
            elif struggle_score > d_threshold[pilot]['high']:
                return "high_effort_consistent_performer"
            else:
                return "efficient_consistent_performer"
        
        # Moderate submission rate (20-80%)
        elif submission_rate >= 0.2:
            if improving:
                return "developing_partial_participant"
            elif struggle_score > d_threshold[pilot]['high']:
                return "struggling_partial_participant"
            else:
                return "inconsistent_participant"
        
        # Low submission rate (0-20%)
        elif submitted > 0:
            if struggle_score > d_threshold[pilot]['high']:
                return "high_effort_minimal_submitter"
            else:
                return "sporadic_minimal_submitter"
        
        # No submissions
        else:
            if struggle_score > d_threshold[pilot]['high']:
                return "engaged_observer"  # High engagement but no submissions
            elif struggle_score > d_threshold[pilot]['low']:
                return "passive_observer"   # Some engagement, no submissions
            else:
                return "disengaged_participant"  # Minimal engagement and no submissions
    
    return "unclassified" 




def generate_assignment_statistics(df: pd.DataFrame, pilot: str = None, assign_ids: list = None, module_id: int = None,
                             course_id:int=None, graph:Neo4jConnection=None, moodle_settings: dict=None, cursor: mysql.connector.cursor.MySQLCursor = None):
        
    # Sanity checks
    if df[df['assign_id'].isin(assign_ids)].shape[0] == 0:
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
        raise ValueError("Unknown pilot")
    
    # Get translation dictionary
    t = translations[language]
    
    # Activity-level statistics
    activity_data = analyze_assignment_statistics(df[df['assign_id'].isin(assign_ids)])
    # Include grades
    activities_ids = [f"ASSIGN:{idx}" for idx in assign_ids]
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
    learner_data = analyze_learner_characteristics(df[df['assign_id'].isin(assign_ids)], pilot=pilot)
    # Include learners interactions
    if not module_id:
        excluded_activies = [f"ASSIGN:{id}" for id in assign_ids]                
        for username, values in learner_data.items():
            for i, attempt in enumerate(values['sessions_details']):            
                attempt['interactions'] = retrieve_learner_interactions(username=username, start_time=attempt['start_time'], end_time=attempt['end_time'], course_id=course_id, excluded_activies=excluded_activies, graph=graph, moodle_settings=moodle_settings, cursor=cursor)

    # ----------------------------------------------------------------------------------
    # Generate activity statistics with translations
    
    if module_id:
        activity_stats = f"### {module_id} - {t['statistics_about_assignment']}\n\n"
        activity_stats += f" - {t['total_assignments']}: {activity_data['total_assignments']}\n"
    else:
        activity_stats = f"### ASSIGN:{assign_ids[0]} - {t['statistics']}\n\n"
            
    activity_stats += f" - {t['total_learners']}: {activity_data['total_users']}\n"
    activity_stats += f" - {t['overall_submission_rate']}: {activity_data['submission_rate']:.1f}%\n"
    activity_stats += f" - {t['average_sessions_per_learner']}: {activity_data['avg_sessions_per_user']:.2f}\n"
    activity_stats += f" - {t['maximum_sessions_by_single_learner']}: {activity_data['max_sessions_by_user']}\n"
    activity_stats += f" - {t['learners_with_multiple_sessions']}: {activity_data['users_with_multiple_sessions']}\n"
    if not module_id:
        activity_stats += f" - {t['peak_activity_hour']}: {activity_data['peak_activity_hour']}:00\n"
        week_day, date = activity_data['peak_activity_day'].split(" ")
        activity_stats += f" - {t['peak_activity_day']}: {t[week_day]} {date}\n"
    
    activity_stats += f"\n**{t['action_distribution']}** ⚙️\n"
    for action, count in activity_data['action_distribution'].items():
        percentage = (count / activity_data['total_actions']) * 100
        activity_stats += f" - {t[action]}: {percentage:.1f}%\n"
    
    activity_stats += f"\n**{t['session_distribution']}** 🔄\n"
    for attempts, count in activity_data['user_session_distribution'].items():
        percentage = (count / activity_data['total_users']) * 100
        activity_stats += f" - {attempts} {t['sessions']}: {percentage:.1f}%\n"

    activity_stats += f"\n\n### {t['learner_behavior_performance']}\n\n"

    # Grades
    if 'Cognitive' in activity_data or 'Communication' in activity_data or 'Creativity' in activity_data or 'Critical_thinking' in activity_data or 'Collaboration' in activity_data:
        activity_stats += f"\n**{t['grades']}** 📊\n"
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
    
    activity_stats += f"\n**{t['engagement_metrics']}** 📊\n"
    avg_submission_rate = sum(values['submission_rate'] for _, values in learner_data.items()) / total_users
    avg_time_spent = sum(values['total_time_spent'] for _, values in learner_data.items()) / total_users
    learners_improving_efficiency = sum(1 for _, values in learner_data.items() if values['improving_efficiency'])

    activity_stats += f" - {t['average_submission_rate_per_learner']}: {avg_submission_rate:.1f}%\n"
    activity_stats += f" - {t['average_time_spent_per_learner']}: {format_time(avg_time_spent, language)}\n"
    activity_stats += f" - {t['learners_showing_efficiency_improvement']}: {(learners_improving_efficiency / total_users) * 100:.1f}%\n"

    # Generate learner statistics with translations
    learner_stats = dict()
    for username, values in learner_data.items():
        learner_stats[username] = f"**{t['learner_engagement_profile']}** 🧑‍🎓\n"
        learner_stats[username] += f" - {t['learner_type']}: {t[values['learner_type']]}\n"
        learner_stats[username] += f" - {t['total_sessions']}: {values['total_sessions']}\n"
        learner_stats[username] += f" - {t['submitted_sessions']}: {values['submitted_sessions']}\n"
        learner_stats[username] += f" - {t['submission_rate']}: {values['submission_rate']:.1f}%\n"
        learner_stats[username] += f" - {t['total_time_spent']}: {format_time(values['total_time_spent'], language)}\n"
        
        if values['total_sessions'] > 1:
            learner_stats[username] += f" - {t['average_time_per_session']}: {format_time(values['avg_time_per_session'], language)}\n"
            efficiency_text = t['yes'] if values['improving_efficiency'] else t['no']
            learner_stats[username] += f" - {t['improving_efficiency']}: {efficiency_text}\n"

        if 'action_frequency' in values:
            learner_stats[username] += f"\n**{t['action_frequency']}** 📈\n"
            for action, count in values['action_frequency'].items():
                learner_stats[username] += f" - {t[action]}: {count}\n"
                
        if not module_id:
            learner_stats[username] += f"\n**{t['session_details']}** 📝\n"
            for i, session in enumerate(values['sessions_details']):
                completed_text = f"{t['submitted_assignment']} ✅" if session['submitted'] else f"{t['not_submitted_assignment']} ❌"                
                learner_stats[username] += f" - {t['session']} {i+1} ({completed_text})\n"
                if session['duration'] > 0:
                    learner_stats[username] += f"    * ⏰ {t['start_session']}: {session['start_time'].strftime('%d-%m-%Y %H:%M:%S')}\n"
                    learner_stats[username] += f"    * 🏁 {t['end_session']}: {session['end_time'].strftime('%d-%m-%Y %H:%M:%S')}\n"                    
                learner_stats[username] += f"    * ⏱️ {t['duration']}: {format_time(session['duration'], language)}\n"
                
                # Include user interactions
                if session['interactions']:
                    learner_stats[username] += f"    * 📚 {t['associated_learning_resources']}: {', '.join(session['interactions'])}\n" 
                    
    return learner_stats, learner_data, activity_stats, activity_data