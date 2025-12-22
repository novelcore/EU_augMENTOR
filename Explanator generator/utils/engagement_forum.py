import pandas as pd
import numpy as np
import mysql.connector
from utils.neo4j_connection import Neo4jConnection
from datetime import datetime, timedelta
from collections import Counter
from utils.utils import format_time
from utils.engagement_utils import retrieve_learner_interactions

d_threshold = {
    "UPAT": {"low": 17, "high": 25},
    "IASIS": {"low": 20, "high": 30},
    "EASD": {"low": 3, "high": 7},
    "KTU": {"low": 3, "high": 7} # TODO: Define thresholds
}

# Translation dictionary
translations = {
    'greek': {
        # Headers
        'forum_statistics': 'Στατιστικά',
        'module_statistics': 'Στατιστικά για Δραστηριότητες Φόρουμ',
        'learner_behavior': 'Συμπεριφορά & Επιδόσεις Μαθητών',
        'learner_engagement_profile': '**Προφίλ Συμμετοχής Μαθητή** 🧑‍🎓',
        
        # Activity statistics
        'total_forums': 'Σύνολο Φόρουμ',
        'total_learners': 'Σύνολο Μαθητών',
        'active_posting_rate': 'Ποσοστό Ενεργής Δημοσίευσης',
        'average_sessions_per_learner': 'Μέσος Όρος Συνεδριών ανά Μαθητή',
        'maximum_sessions_by_single_user': 'Μέγιστες Συνεδρίες από Έναν Χρήστη',
        'users_with_multiple_sessions': 'Χρήστες με Πολλαπλές Συνεδρίες',
        'average_posts_per_active_user': 'Μέσος Όρος Δημοσιεύσεων ανά Ενεργό Χρήστη',
        'peak_activity_hour': 'Ώρα Μέγιστης Δραστηριότητας',
        'peak_activity_day': 'Ημέρα Μέγιστης Δραστηριότητας',
        
        # Sections
        'action_distribution': '**Κατανομή Ενεργειών** ⚙️',
        'session_distribution': '**Κατανομή Συνεδριών** 🔄',
        'grade': '**Βαθμολογία** 📊',
        'learner_type_distribution': '**Κατανομή Τύπου Μαθητή** 🧠',
        'engagement_metrics': '**Μετρήσεις Συμμετοχής** 📊',
        'action_metrics': '**Μετρήσεις Ενεργειών** 📊',
        'advanced_metrics': '**Προηγμένες Μετρήσεις** 🔍',
        'action_breakdown': '**Ανάλυση Ενεργειών**',
        'detailed_action_frequency': '**Λεπτομερής Συχνότητα Ενεργειών**',
        'session_details': '**Λεπτομέρειες Συνεδρίας**',
        'start_session': 'Έναρξη συνεδρίας',
        'end_session': 'Τερματισμός συνεδρίας',
        
        # Grades
        'cognitive': 'Γνωστικό',
        'communication': 'Επικοινωνία',
        'creativity': 'Δημιουργικότητα',
        'critical_thinking': 'Κριτική Σκέψη',
        'collaboration': 'Συνεργασία',
        
        # Engagement metrics
        'average_posting_rate_per_learner': 'Μέσος Όρος Ποσοστού Δημοσίευσης ανά Μαθητή',
        'average_time_spent_per_learner': 'Μέσος Όρος Χρόνου ανά Μαθητή',
        'learners_with_consistent_posting': 'Μαθητές με Συνεπή Δημοσίευση',
        'learners_showing_improved_engagement': 'Μαθητές με Βελτιωμένη Συμμετοχή',
        
        # Action metrics
        'average_creates_per_learner': 'Μέσος Όρος *Δημιουργιών* ανά Μαθητή',
        'average_posts_per_learner': 'Μέσος Όρος *Δημοσιεύσεων* ανά Μαθητή',
        'average_replies_per_learner': 'Μέσος Όρος *Απαντήσεων* ανά Μαθητή',
        'average_views_per_learner': 'Μέσος Όρος *Προβολών* ανά Μαθητή',
        
        # Learner profile
        'learner_type': 'Τύπος Μαθητή',
        'total_sessions': 'Σύνολο Συνεδριών',
        'posting_sessions': 'Συνεδρίες Δημοσίευσης',
        'view_only_sessions': 'Συνεδρίες Μόνο Προβολής',
        'posting_rate': 'Ποσοστό Δημοσίευσης',
        'total_time_spent': 'Συνολικός Χρόνος',
        'average_time_per_session': 'Μέσος Όρος Χρόνου ανά Συνεδρία',
        'engagement_score': 'Βαθμολογία Συμμετοχής',
        'disengagement_risk_score': 'Βαθμολογία Κινδύνου Αποσύνδεσης',
        'unique_forums': 'Μοναδικά Φόρουμ',
        'forum_diversity': 'Ποικιλομορφία Φόρουμ',
        'consistent_participation': 'Συνεπής Συμμετοχή',
        'improving_engagement': 'Βελτιούμενη Συμμετοχή',
        
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
        'posts': 'Δημοσιεύσεις (posts)',
        'total_actions': 'Σύνολο Ενεργειών',
       
        # Session details
        'session': 'Συνεδρία',
        'duration': 'Διάρκεια',
        'associated_learning_resources': 'Σχετικοί εκπαιδευτικοί πόροι που έγιναν πρόσβαση κατά τη συνεδρία',
        'sessions_text': 'συνεδρία(ες)',
        'min': 'λεπτά',
        'yes': 'Ναι',
        'no': 'Όχι',
        
        # Days of the week
        'Monday': 'Δευτέρα',
        'Tuesday': 'Τρίτη',
        'Wednesday': 'Τετάρτη',
        'Thursday': 'Πέμπτη',
        'Friday': 'Παρασκευή',
        'Saturday': 'Σάββατο',
        'Sunday': 'Κυριακή',
        
        # Learner type categories
        'one_time_active_contributor': 'Μία Φορά Ενεργός Συνεισφέρων',
        'one_time_basic_poster': 'Μία Φορά Βασικός Δημοσιευτής',
        'one_time_lurker': 'Μία Φορά Παρατηρητής',
        'highly_active_contributor': 'Πολύ Ενεργός Συνεισφέρων',
        'regular_contributor': 'Τακτικός Συνεισφέρων',
        'occasional_contributor': 'Περιστασιακός Συνεισφέρων',
        'selective_active_learner': 'Επιλεκτικός Ενεργός Μαθητής',
        'moderate_learner': 'Μέτριος Μαθητής',
        'mostly_lurker_with_some_posts': 'Κυρίως Παρατηρητής με Μερικές Δημοσιεύσεις',
        'active_lurker': 'Ενεργός Παρατηρητής',
        'basic_lurker': 'Βασικός Παρατηρητής',
        'unclassified': 'Μη Κατηγοριοποιημένος',
 
    },
    'serbian': {
        # Headers
        'forum_statistics': 'Statistike',
        'module_statistics': 'Statistike za Aktivnosti Foruma',
        'learner_behavior': 'Ponašanje i performanse učenika',
        'learner_engagement_profile': '**Profil Angažovanja Učenika** 🧑‍🎓',
        
        # Activity statistics
        'total_forums': 'Ukupno Foruma',
        'total_learners': 'Ukupno Učenika',
        'active_posting_rate': 'Stopa Aktivnog Objavljivanja',
        'average_sessions_per_learner': 'Prosečno Sesija po Učeniku',
        'maximum_sessions_by_single_user': 'Maksimalno Sesija od Jednog Korisnika',
        'users_with_multiple_sessions': 'Korisnici sa Više Sesija',
        'average_posts_per_active_user': 'Prosečno Objava po Aktivnom Korisniku',
        'peak_activity_hour': 'Vreme Najveće Aktivnosti',
        'peak_activity_day': 'Dan Najveće Aktivnosti',
        
        # Sections
        'action_distribution': '**Distribucija Akcija** ⚙️',
        'session_distribution': '**Distribucija Sesija** 🔄',
        'grade': '**Ocena** 📊',
        'learner_type_distribution': '**Distribucija Tipova Učenika** 🧠',
        'engagement_metrics': '**Metrije Angažovanja** 📊',
        'action_metrics': '**Metrije Akcija** 📊',
        'advanced_metrics': '**Napredne Metrije** 🔍',
        'action_breakdown': '**Analiza Akcija**',
        'detailed_action_frequency': '**Detaljna Frekvencija Akcija**',
        'session_details': '**Detalji Sesije**',
        'start_session': 'Početak sesije',
        'end_session': 'Završetak sesije',
                
        # Grades
        'cognitive': 'Kognitivno',
        'communication': 'Komunikacija',
        'creativity': 'Kreativnost',
        'critical_thinking': 'Kritičko Razmišljanje',
        'collaboration': 'Saradnja',
        
        # Engagement metrics
        'average_posting_rate_per_learner': 'Prosečna Stopa Objavljivanja po Učeniku',
        'average_time_spent_per_learner': 'Prosečno Vreme po Učeniku',
        'learners_with_consistent_posting': 'Učenici sa Doslednim Objavljivanjem',
        'learners_showing_improved_engagement': 'Učenici sa Poboljšanim Angažovanjem',
        
        # Action metrics
        'average_creates_per_learner': 'Prosečno *Kreacija* po Učeniku',
        'average_posts_per_learner': 'Prosečno *Objava* po Učeniku',
        'average_replies_per_learner': 'Prosečno *Odgovora* po Učeniku',
        'average_views_per_learner': 'Prosečno *Prikaza* po Učeniku',
        
        # Learner profile
        'learner_type': 'Tip Učenika',
        'total_sessions': 'Ukupno Sesija',
        'posting_sessions': 'Sesije Objavljivanja',
        'view_only_sessions': 'Sesije Samo Pregledanja',
        'posting_rate': 'Stopa Objavljivanja',
        'total_time_spent': 'Ukupno Vreme',
        'average_time_per_session': 'Prosečno Vreme po Sesiji',
        'engagement_score': 'Skor Angažovanja',
        'disengagement_risk_score': 'Skor Rizika od Prestanka Angažovanja',
        'unique_forums': 'Jedinstveni Forumi',
        'forum_diversity': 'Raznolikost Foruma',
        'consistent_participation': 'Dosledna Participacija',
        'improving_engagement': 'Poboljšano Angažovanje',
        
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
        'posts': 'Objave (posts)',
        'total_actions': 'Ukupno Akcija',
                
        # Session details
        'session': 'Sesija',
        'duration': 'Trajanje',
        'associated_learning_resources': 'Resursi za učenje dostupni tokom pokušaja', # 'Povezani obrazovni resursi kojima je pristupano tokom sesije',
        'sessions_text': 'sesija(e)',
        'min': 'min',
        'yes': 'Da',
        'no': 'Ne',
        
        # Days of the week
        'Monday': 'Ponedeljak',
        'Tuesday': 'Utorak',
        'Wednesday': 'Sreda',
        'Thursday': 'Četvrtak',
        'Friday': 'Petak',
        'Saturday': 'Subota',
        'Sunday': 'Nedelja',        
        
        # Learner type categories
        'one_time_active_contributor': 'Jednokratni Aktivni Saradnik',
        'one_time_basic_poster': 'Jednokratni Osnovni Objavljač',
        'one_time_lurker': 'Jednokratni Posmatrač',
        'highly_active_contributor': 'Visoko Aktivni Saradnik',
        'regular_contributor': 'Redovni Saradnik',
        'occasional_contributor': 'Povremeni Saradnik',
        'selective_active_learner': 'Selektivni Aktivni Učenik',
        'moderate_learner': 'Umeren Učenik',
        'mostly_lurker_with_some_posts': 'Uglavnom Posmatrač sa Nekim Objavama',
        'active_lurker': 'Aktivni Posmatrač',
        'basic_lurker': 'Osnovni Posmatrač',
        'unclassified': 'Neklasifikovan',
        

    },
    'english': {
        # Headers
        'forum_statistics': 'Statistics',
        'module_statistics': 'Forum Activity Statistics',
        'learner_behavior': 'Learner Behavior & Performance',
        'learner_engagement_profile': '**Learner Engagement Profile** 🧑‍🎓',
        
        # Activity statistics
        'total_forums': 'Total Forums',
        'total_learners': 'Total Learners',
        'active_posting_rate': 'Active Posting Rate',
        'average_sessions_per_learner': 'Average Sessions per Learner',
        'maximum_sessions_by_single_user': 'Maximum Sessions by a Single User',
        'users_with_multiple_sessions': 'Users with Multiple Sessions',
        'average_posts_per_active_user': 'Average Posts per Active User',
        'peak_activity_hour': 'Peak Activity Hour',
        'peak_activity_day': 'Peak Activity Day',
        
        # Sections
        'action_distribution': '**Action Distribution** ⚙️',
        'session_distribution': '**Session Distribution** 🔄',
        'grade': '**Grade** 📊',
        'learner_type_distribution': '**Learner Type Distribution** 🧠',
        'engagement_metrics': '**Engagement Metrics** 📊',
        'action_metrics': '**Action Metrics** 📊',
        'advanced_metrics': '**Advanced Metrics** 🔍',
        'action_breakdown': '**Action Breakdown**',
        'detailed_action_frequency': '**Detailed Action Frequency**',
        'session_details': '**Session Details**',
        'start_session': 'Start Session',
        'end_session': 'End Session',
        
        # Grades
        'cognitive': 'Cognitive',
        'communication': 'Communication',
        'creativity': 'Creativity',
        'critical_thinking': 'Critical Thinking',
        'collaboration': 'Collaboration',
        
        # Engagement metrics
        'average_posting_rate_per_learner': 'Average Posting Rate per Learner',
        'average_time_spent_per_learner': 'Average Time Spent per Learner',
        'learners_with_consistent_posting': 'Learners with Consistent Posting',
        'learners_showing_improved_engagement': 'Learners Showing Improved Engagement',
        
        # Action metrics
        'average_creates_per_learner': 'Average *Creates* per Learner',
        'average_posts_per_learner': 'Average *Posts* per Learner',
        'average_replies_per_learner': 'Average *Replies* per Learner',
        'average_views_per_learner': 'Average *Views* per Learner',
        
        # Learner profile
        'learner_type': 'Learner Type',
        'total_sessions': 'Total Sessions',
        'posting_sessions': 'Posting Sessions',
        'view_only_sessions': 'View-Only Sessions',
        'posting_rate': 'Posting Rate',
        'total_time_spent': 'Total Time Spent',
        'average_time_per_session': 'Average Time per Session',
        'engagement_score': 'Engagement Score',
        'disengagement_risk_score': 'Disengagement Risk Score',
        'unique_forums': 'Unique Forums',
        'forum_diversity': 'Forum Diversity',
        'consistent_participation': 'Consistent Participation',
        'improving_engagement': 'Improving Engagement',
        
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
                
        'posts': 'Posts',
        'total_actions': 'Total Actions',
        
        # Session details
        'session': 'Session',
        'duration': 'Duration',
        'associated_learning_resources': 'Associated Learning Resources Accessed During the Session',
        'sessions_text': 'session(s)',
        'min': 'min',
        'yes': 'Yes',
        'no': 'No',
        
        # Days of the week
        'Monday': 'Monday',
        'Tuesday': 'Tuesday',
        'Wednesday': 'Wednesday',
        'Thursday': 'Thursday',
        'Friday': 'Friday',
        'Saturday': 'Saturday',
        'Sunday': 'Sunday',
        
        # Learner type categories
        'one_time_active_contributor': 'One-Time Active Contributor',
        'one_time_basic_poster': 'One-Time Basic Poster',
        'one_time_lurker': 'One-Time Lurker',
        'highly_active_contributor': 'Highly Active Contributor',
        'regular_contributor': 'Regular Contributor',
        'occasional_contributor': 'Occasional Contributor',
        'selective_active_learner': 'Selective Active Learner',
        'moderate_learner': 'Moderate Learner',
        'mostly_lurker_with_some_posts': 'Mostly Lurker with Some Posts',
        'active_lurker': 'Active Lurker',
        'basic_lurker': 'Basic Lurker',
        'unclassified': 'Unclassified',
    }    
}
    
def identify_discussion_sessions(df):
    """
    Identifies individual discussion sessions by grouping user actions based on time gaps
    and discussion thread participation.

    A new session is started if:
    - More than 2 hours (7200 seconds) have passed since the last action, or
    - The user switches to a different discussion thread ('forum_id').

    Parameters:
    ----------
    df : pandas.DataFrame
        DataFrame containing user discussion activity with at least the following columns:
        - 'username': User identifier.
        - 'action_time_unix': UNIX timestamp of the action.
        - 'forum_id': Identifier of the discussion forum or thread.

    Returns:
    -------
    pandas.DataFrame
        A copy of the input DataFrame with an added 'session_number' column that
        indicates the session grouping for each user’s discussion activity.
    """
    df_with_sessions = df.copy()
    df_with_sessions["session_number"] = 0

    for username in df["username"].unique():
        user_data = df[df["username"] == username].sort_values("action_time_unix")
        session_num = 1
        last_time = None
        last_discussion = None

        for idx, row in user_data.iterrows():
            # Start new session if more than 2 hours gap or different discussion
            if (
                last_time is None
                or (row["action_time_unix"] - last_time) > 7200  # 2 hours
                or (last_discussion is not None and row["forum_id"] != last_discussion)
            ):
                if last_time is not None:
                    session_num += 1

            df_with_sessions.loc[idx, "session_number"] = session_num
            last_time = row["action_time_unix"]
            last_discussion = row["forum_id"]

    return df_with_sessions


def analyze_single_discussion_session(session_data):
    """
    Analyze a single forum discussion session, summarizing user activity and engagement.

    The analysis includes session duration, action counts, time intervals between actions,
    participation types (posting, replying, viewing), number of unique forums involved,
    and the chronological sequence of actions.

    Parameters:
    ----------
    session_data : pandas.DataFrame
        DataFrame containing activity data for a single user discussion session. Expected columns:
        - 'action_time_unix': UNIX timestamp of the action.
        - 'action_time_readable': datetime of the action.
        - 'action': type of action (e.g., 'created', 'posted', 'replied', 'viewed').
        - 'forum_id': identifier of the discussion forum/thread.

    Returns:
    -------
    dict or None
        Dictionary summarizing the session with keys:
        - 'duration': Total session length in secs.
        - 'total_actions': Number of recorded actions in the session.
        - 'action_counts': Dictionary of action types and their counts.
        - 'avg_time_between_actions': Average time in seconds between consecutive actions.
        - 'max_gap': Maximum gap in seconds between actions.
        - 'posted': Boolean indicating if user created or posted content.
        - 'replied': Boolean indicating if user replied to posts.
        - 'viewed': Boolean indicating if user viewed content.
        - 'unique_forums': Number of unique forums/thread IDs involved in the session.
        - 'action_sequence': String representing chronological sequence of actions.
        - 'start_time': Datetime of first action.
        - 'end_time': Datetime of last action.

        Returns None if input data is empty.
    """
    if len(session_data) == 0:
        return None

    # Sort by time
    session_data = session_data.sort_values("action_time_unix")

    # Calculate session duration
    start_time = session_data["action_time_readable"].iloc[0]
    end_time = session_data["action_time_readable"].iloc[-1]
    duration = (end_time - start_time).total_seconds()

    # Count actions
    action_counts = session_data["action"].value_counts().to_dict()

    # Calculate time gaps
    time_diffs = session_data["action_time_readable"].diff().dt.total_seconds()
    avg_time_between_actions = time_diffs.mean() if len(time_diffs) > 1 else 0
    max_gap = time_diffs.max() if len(time_diffs) > 1 else 0

    # Check participation types
    posted = (
        "created" in session_data["action"].values
        or "posted" in session_data["action"].values
    )
    replied = "replied" in session_data["action"].values
    viewed = "viewed" in session_data["action"].values

    # Count unique forums participated in
    unique_forums = session_data["forum_id"].nunique()

    # Get action sequence
    action_sequence = " -> ".join(session_data["action"].tolist())

    return {
        "duration": duration,
        "total_actions": len(session_data),
        "action_counts": action_counts,
        "avg_time_between_actions": avg_time_between_actions,
        "max_gap": max_gap,
        "posted": posted,
        "replied": replied,
        "viewed": viewed,
        "unique_forums": unique_forums,
        "action_sequence": action_sequence,
        "start_time": start_time,
        "end_time": end_time,
    }


def analyze_forum_statistics(df):
    """
    Analyze overall forum participation and activity patterns in a course.

    This function aggregates forum interaction data across all users to compute
    statistics related to session counts, posting behavior, time-of-day trends,
    and action frequencies.

    Parameters:
    ----------
    df : pandas.DataFrame
        DataFrame containing forum activity data with at least the following columns:
        - 'username': User identifier.
        - 'forum_id': Identifier of the discussion forum or thread.
        - 'action': Type of forum action (e.g., 'created', 'posted', 'replied', 'viewed').
        - 'action_time_readable': Timestamp (datetime) of the action.
        - 'action_time_unix': UNIX timestamp of the action.

    Returns:
    -------
    dict
        Dictionary of course-wide forum statistics including:
        - 'total_users': Number of unique users.
        - 'total_forums': Number of unique forum threads.
        - 'total_actions': Total number of forum-related actions.
        - 'posting_rate': Percentage of users who actively posted or replied.
        - 'avg_sessions_per_user': Average number of discussion sessions per user.
        - 'max_sessions_by_user': Maximum number of sessions by a single user.
        - 'users_with_multiple_sessions': Count of users with more than one session.
        - 'avg_posts_per_active_user': Average number of posts/replies per active user.
        - 'peak_activity_hour': Hour of day with the most activity.
        - 'peak_activity_day': Day of the week with the most activity.
        - 'most_common_action': Most frequently performed forum action.
        - 'action_distribution': Series showing frequency of each action type.
        - 'user_session_distribution': Series showing count of users by number of sessions.
    """
    df_sessions = identify_discussion_sessions(df)

    # Basic course info
    total_users = df["username"].nunique()
    total_forums = df["forum_id"].nunique()
    total_actions = len(df)

    # Session analysis
    user_session_counts = (
        df_sessions.groupby("username")["session_number"].max().reset_index()
    )
    user_session_counts["total_sessions"] = user_session_counts["session_number"]

    # Participation rates
    active_posters = df[df["action"].isin(["created", "posted", "replied"])][
        "username"
    ].nunique()
    posting_rate = (active_posters / total_users) * 100

    # Time analysis
    df["hour"] = df["action_time_readable"].dt.hour
    df["day_of_week"] = df["action_time_readable"].dt.day_name()

    # Most active times
    peak_hour = df["hour"].mode().iloc[0] if not df["hour"].empty else None
    peak_day = (
        f"{df['day_of_week'].mode().iloc[0]} ({df['action_time_readable'].iloc[0].date().isoformat()})"
        if not df["day_of_week"].empty
        else None
    )

    # Action frequency
    action_distribution = df["action"].value_counts()
    most_common_action = (
        action_distribution.index[0] if not action_distribution.empty else None
    )

    # Discussion participation
    posts_per_user = (
        df[df["action"].isin(["created", "posted", "replied"])]
        .groupby("username")
        .size()
    )

    return {
        "total_users": total_users,
        "total_forums": total_forums,
        "total_actions": total_actions,
        "posting_rate": posting_rate,
        "avg_sessions_per_user": user_session_counts["total_sessions"].mean(),
        "max_sessions_by_user": user_session_counts["total_sessions"].max(),
        "users_with_multiple_sessions": (
            user_session_counts["total_sessions"] > 1
        ).sum(),
        "avg_posts_per_active_user": posts_per_user.mean()
        if len(posts_per_user) > 0
        else 0,
        "peak_activity_hour": peak_hour,
        "peak_activity_day": peak_day,
        "most_common_action": most_common_action,
        "action_distribution": action_distribution,
        "user_session_distribution": user_session_counts["total_sessions"]
        .value_counts()
        .sort_index(),
    }


def analyze_forum_learner_characteristics(df, pilot):
    """
    Analyze individual forum learner characteristics across all discussion sessions.

    This function examines each user's forum behavior over time by analyzing their
    session-level activity (e.g., posts, replies, views), participation consistency,
    engagement, and disengagement risk. It also classifies users into forum learner types.

    Parameters:
    ----------
    df : pandas.DataFrame
        DataFrame containing raw forum activity logs for all users.
        Required columns:
        - 'username': User identifier
        - 'forum_id': Forum/thread identifier
        - 'action': Action type (e.g., 'created', 'posted', 'replied', 'viewed')
        - 'action_time_unix': Timestamp in UNIX format
        - 'action_time_readable': Timestamp in datetime format
    pilot : str
        Identifier for the pilot group (used to access engagement thresholds).

    Returns:
    -------
    dict
        A dict where each element is a dictionary representing a learner's profile with keys:
        - 'total_sessions': Total number of discussion sessions
        - 'posting_sessions': Number of sessions where the user posted or replied
        - 'view_only_sessions': Number of sessions where the user only viewed content
        - 'total_time_spent': Total time spent across all sessions
        - 'total_actions': Total number of actions recorded
        - 'total_clicks': total number of clicks        
        - 'avg_time_per_session': Average duration per session (in seconds)
        - 'posting_rate': Percentage of sessions that included posting/replying
        - 'consistent_participation': Boolean indicating regular contribution
        - 'engagement_score': Weighted score based on types of participation
        - 'unique_forums': Number of distinct forums visited
        - 'forum_diversity': Ratio of unique forums to sessions
        - 'disengagement_risk_score': Composite score indicating risk of disengagement
        - 'improving_engagement': Boolean indicating rising activity across sessions
        - 'learner_type': Categorical label describing user behavior
        - 'action_frequency': Dictionary of action type counts
        - 'sessions_details': List of detailed session-level summaries
    """
    df_sessions = identify_discussion_sessions(df)
    learner_profiles = dict()

    for username in df["username"].unique():
        user_data = df_sessions[df_sessions["username"] == username]

        # Basic info
        total_sessions = user_data["session_number"].max()
        total_actions = len(user_data)
        total_clicks = len(user_data[user_data['action'] != "autosaved"])

        # Analyze each session
        sessions_analysis = []
        for session_num in range(1, total_sessions + 1):
            session_data = user_data[user_data["session_number"] == session_num]
            session_analysis = analyze_single_discussion_session(session_data)
            if session_analysis:
                sessions_analysis.append(session_analysis)

        if not sessions_analysis:
            continue

        # Calculate overall metrics
        total_time_spent = sum([sess["duration"] for sess in sessions_analysis])

        # Behavioral patterns
        all_actions = user_data["action"].tolist()
        action_frequency = Counter(all_actions)

        # IMPROVED: Calculate specific action counts
        total_creates = action_frequency.get("created", 0)
        total_uploaded = action_frequency.get("uploaded", 0)
        total_replies = action_frequency.get("replied", 0)
        total_viewed = action_frequency.get("viewed", 0)
        total_updated = action_frequency.get("updated", 0)       
            
        # Participation analysis
        posting_sessions = sum(
            [1 for sess in sessions_analysis if sess["posted"] or sess["replied"]]
        )
        view_only_sessions = sum(
            [
                1
                for sess in sessions_analysis
                if sess["viewed"] and not (sess["posted"] or sess["replied"])
            ]
        )

        # Consistency analysis
        consistent_participation = (
            posting_sessions > 0 and posting_sessions / total_sessions > 0.3
        )

        # IMPROVED: Calculate engagement score with clearer variable names
        total_posts = total_creates + total_uploaded + total_replies
        # For engagement scoring (avoid double counting)
        engagement_score = (
            total_creates * 3  # Creating discussions worth more
            + total_replies * 2  # Replying worth medium
            + total_uploaded * 1.5  # Uploading worth medium-low
            + total_updated * 0.5  # Updating worth less
            + (total_time_spent) * 0.5
        )  # Time spent factor

        # Discussion breadth
        unique_forums = user_data["forum_id"].nunique()
        forum_diversity = unique_forums / total_sessions if total_sessions > 0 else 0

        # Calculate disengagement risk score
        # Higher score = higher risk of disengagement
        avg_gap = np.mean(
            [
                sess["avg_time_between_actions"]
                for sess in sessions_analysis
                if sess["avg_time_between_actions"] > 0
            ]
        )
        if np.isnan(avg_gap):
            avg_gap = 0

        disengagement_risk_score = (
            (view_only_sessions / total_sessions * 0.4)  # High view-only sessions (40%)
            + (max(0, 5 - engagement_score) / 5 * 0.3)  # Low engagement (30%)
            + (min(avg_gap, 30) / 30 * 0.2)  # Long gaps between actions (20%)
            + (max(0, 3 - total_sessions) / 3 * 0.1)  # Few sessions (10%)
        )

        # Improvement tracking (comparing early vs late sessions)
        improving_engagement = False
        if len(sessions_analysis) > 2:
            early_engagement = np.mean(
                [
                    sess["total_actions"]
                    for sess in sessions_analysis[: len(sessions_analysis) // 2]
                ]
            )
            late_engagement = np.mean(
                [
                    sess["total_actions"]
                    for sess in sessions_analysis[len(sessions_analysis) // 2 :]
                ]
            )
            improving_engagement = (
                late_engagement > early_engagement * 1.1
            )  # 10% improvement

        # Categorize learner
        learner_type = categorize_forum_learner(
            total_sessions,
            pilot,
            engagement_score,
            posting_sessions,
            view_only_sessions,
            consistent_participation,
        )

        learner_profiles[username] = {
            "total_sessions": total_sessions,
            "posting_sessions": posting_sessions,
            "view_only_sessions": view_only_sessions,
            "total_time_spent": total_time_spent,
            "total_actions": total_actions,
            "total_clicks": total_clicks,
            #
            "total_creates": total_creates,
            "total_uploaded": total_uploaded,
            "total_replies": total_replies,
            "total_posts": total_posts,
            "total_viewed": total_viewed,                        
            #
            "avg_time_per_session": total_time_spent / total_sessions
            if total_sessions > 0
            else 0,
            "posting_rate": (posting_sessions / total_sessions) * 100
            if total_sessions > 0
            else 0,
            "consistent_participation": consistent_participation,
            "engagement_score": engagement_score,
            "unique_forums": unique_forums,
            "forum_diversity": forum_diversity,
            "disengagement_risk_score": disengagement_risk_score,
            "improving_engagement": improving_engagement,
            "learner_type": learner_type,
            "action_frequency": dict(action_frequency),
            "sessions_details": sessions_analysis,
        }

    return learner_profiles


def categorize_forum_learner(
    sessions, pilot, engagement_score, posting_sessions, view_only_sessions, consistent
):
    """
    Categorizes learners based on their forum activity, considering posting frequency,
    engagement score, and consistency across sessions.

    Args:
        sessions (int): Total number of forum sessions the learner engaged with.
        pilot (str): Pilot group identifier, used to access threshold values for engagement.
        engagement_score (float): A metric indicating the learner's level of interaction or effort.
        posting_sessions (int): Number of sessions where the learner made posts.
        view_only_sessions (int): Number of sessions where the learner only viewed without posting.
        consistent (bool): Whether the learner consistently engaged across sessions.

    Returns:
        str: A descriptive category label representing the learner's forum engagement behavior.

    Categories:
        - "One-Time Active Contributor":
            Participated in only one session with a post and high engagement.
        - "One-Time Basic Poster":
            Participated in only one session with a post and low/moderate engagement.
        - "One-Time Lurker":
            Participated in only one session without posting.
        - "Highly Active Contributor":
            Posted in more than 70% of sessions with high engagement.
        - "Regular Contributor":
            Posted in more than 70% of sessions and engaged consistently.
        - "Occasional Contributor":
            Posted in more than 70% of sessions but inconsistently and with moderate/low engagement.
        - "Selective Active learner":
            Posted in 30–70% of sessions with high engagement.
        - "Moderate learner":
            Posted in 30–70% of sessions with moderate or low engagement.
        - "Mostly Lurker with Some Posts":
            Posted in fewer than 30% of sessions but has at least one post.
        - "Active Lurker":
            Never posted, but engagement score indicates active reading or attention.
        - "Basic Lurker":
            No posts and low engagement across sessions.
        - "Unclassified":
            Fallback category for edge cases or invalid input.

    Notes:
        - Posting ratio is computed as `posting_sessions / sessions`.
        - Engagement thresholds are retrieved from `d_threshold[pilot]['high']` and `['low']`.
    """


    posting_ratio = posting_sessions / sessions if sessions > 0 else 0

    if sessions == 1:
        if posting_sessions == 1:
            if engagement_score > d_threshold[pilot]['high']:
                return "one_time_active_contributor"
            else:
                return "one_time_basic_poster"
        else:
            return "one_time_lurker"

    elif sessions > 1:
        if posting_ratio > 0.7:  # Posts in most sessions
            if engagement_score > d_threshold[pilot]['high']:
                return "highly_active_contributor"
            elif consistent:
                return "regular_contributor"
            else:
                return "occasional_contributor"
        elif posting_ratio > 0.3:  # Posts in some sessions
            if engagement_score > d_threshold[pilot]['high']:
                return "selective_active_learner"
            else:
                return "moderate_learner"
        elif posting_sessions > 0:
            return "mostly_lurker_with_some_posts"
        else:
            if engagement_score > d_threshold[pilot]['low']:
                return "active_lurker"
            else:
                return "basic_lurker"

    return "unclassified"



def generate_forum_statistics(
    df: pd.DataFrame, pilot: str = None, forum_ids: list = None, module_id: int = None,
    course_id:int=None, graph:Neo4jConnection=None, moodle_settings: dict=None, 
    cursor: mysql.connector.cursor.MySQLCursor = None):
    """
        Generates detailed learner-level and course-level statistics for Moodle forum activity.

        This function analyzes forum logs to extract insights on learner engagement, forum usage patterns,
        and behavioral characteristics. It supports multi-forum or single-forum analysis and integrates
        additional learning resource interaction data for contextual enrichment.

        Args:
            df (pd.DataFrame): DataFrame containing forum interaction logs. Must include columns such as
                            'forum_id', 'username', 'action', 'timestamp', etc.
            pilot (str): Identifier for the pilot group used to retrieve threshold values for engagement categorization.
            forum_ids (list): List of forum IDs to include in the analysis.
            module_id (int, optional): Course module ID used for labeling multi-forum analysis summaries.
            course_id (int, optional): Course IDs used when retrieving resource interaction data.
            graph (Neo4jConnection, optional): Graph database connection used to query learner-resource interactions.
            moodle_settings (dict, optional): Moodle configuration used in resource interaction lookups.
            cursor (mysql.connector.cursor.MySQLCursor, optional): MySQL cursor for querying Moodle database tables.

        Returns:
            tuple:
                learner_stats (dict): Mapping of usernames to their personalized forum engagement profiles.
                    Includes:
                        - Learner type classification
                        - Posting vs viewing session data
                        - Time spent, session summaries
                        - Posting and thread creation counts
                        - Consistency and improvement indicators
                learner_data (dict): Raw structured statistics per learner, including numeric engagement metrics.
                activity_stats (str): Multi-section formatted string summarizing course/module-level statistics.
                    Includes:
                        - Learner counts and posting rates
                        - Action and session distributions
                        - Learner type proportions
                        - Aggregate engagement trends
                        - Posting/thread creation totals
                activity_data (dict): Structured summary of overall forum/module activity metrics, including distributions.

        Raises:
            Exception: If no learners are found within the specified forum(s).
            ValueError: If the `pilot` parameter is missing (required for learner classification logic).

        Notes:
            - Assumes availability of external functions: `analyze_forum_statistics`,
            `analyze_forum_learner_characteristics`, `format_time`, and `retrieve_learner_interactions`.
            - Relies on `d_threshold[pilot]` to classify learners by type and engagement thresholds.
            - Supports forum-level or module-level aggregation based on the number of forums provided.
    """
    # Sanity checks
    if df[df["forum_id"].isin(forum_ids)].shape[0] == 0:
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
    
    # Get translations for the selected language
    t = translations[language]
    
    # Activity-level statistics
    activity_data = analyze_forum_statistics(df[df["forum_id"].isin(forum_ids)])
    # Include grades
    activities_ids = [f"FORUM:{idx}" for idx in forum_ids]
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
    learner_data = analyze_forum_learner_characteristics(
        df=df[df["forum_id"].isin(forum_ids)], pilot=pilot
    )
    # Include learners interactions
    if not module_id:
        excluded_activies = [f"FORUM:{id}" for id in forum_ids]
        for username, values in learner_data.items():
            for i, session in enumerate(values['sessions_details']):
                session['interactions'] = retrieve_learner_interactions(username=username, start_time=session['start_time'], end_time=session['end_time'], course_id=course_id, excluded_activies=excluded_activies, graph=graph, moodle_settings=moodle_settings, cursor=cursor)

    # ----------------------------------------------------------------------------------
    
    if module_id:
        activity_stats = f"## {module_id} - {t['module_statistics']}\n\n"
        activity_stats += f" - {t['total_forums']}: {activity_data['total_forums']}\n"
    else:
        activity_stats = f"## FORUM:{forum_ids[0]} - {t['forum_statistics']}\n\n"
           
    activity_stats += f" - {t['total_learners']}: {activity_data['total_users']}\n"
    activity_stats += f" - {t['active_posting_rate']}: {activity_data['posting_rate']:.1f}%\n"
    activity_stats += f" - {t['average_sessions_per_learner']}: {activity_data['avg_sessions_per_user']:.2f}\n"
    activity_stats += f" - {t['maximum_sessions_by_single_user']}: {activity_data['max_sessions_by_user']}\n"
    activity_stats += f" - {t['users_with_multiple_sessions']}: {activity_data['users_with_multiple_sessions']}\n"
    activity_stats += f" - {t['average_posts_per_active_user']}: {activity_data['avg_posts_per_active_user']:.2f}\n"
    if not module_id:
        activity_stats += f" - {t['peak_activity_hour']}: {activity_data['peak_activity_hour']}:00\n"
        week_day, date = activity_data['peak_activity_day'].split(" ")
        activity_stats += f" - {t['peak_activity_day']}: {t[week_day]} {date}\n"
        
    activity_stats += f"\n{t['action_distribution']}\n"
    for action, count in activity_data["action_distribution"].items():
        percentage = (count / activity_data["total_actions"]) * 100
        activity_stats += f" - {t[action]}: {percentage:.1f}%\n"

    activity_stats += f"\n{t['session_distribution']}\n"
    for sessions, count in activity_data["user_session_distribution"].items():
        percentage = (count / activity_data["total_users"]) * 100
        activity_stats += f" - {sessions} {t['sessions_text']}: {percentage:.1f}%\n"


    activity_stats += f"\n\n### {t['learner_behavior']}\n\n"
    
    # Grades
    if 'Cognitive' in activity_data or 'Communication' in activity_data or 'Creativity' in activity_data or 'Critical_thinking' in activity_data or 'Collaboration' in activity_data:
        activity_stats += f"{t['grade']}\n"
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

    activity_stats += f"\n{t['learner_type_distribution']}\n"
    for learner_type, count in learner_type_counts.items():
        percentage = (count / total_users) * 100
        activity_stats += f" - {t[learner_type]}: {percentage:.1f}%\n"

    # Engagement metrics   
    avg_posting_rate = (
        sum(values["posting_rate"] for username, values in learner_data.items())
        / total_users
    )
    avg_time_spent = (
        sum(
            values["total_time_spent"]
            for username, values in learner_data.items()
        )
        / total_users
    )

    consistent_users = sum(
        values["consistent_participation"] for username, values in learner_data.items()
    )
    improving_users = sum(
        1 for _, values in learner_data.items() if values["improving_engagement"]
    )
    activity_stats += f"\n{t['engagement_metrics']}\n"
    activity_stats += f" - {t['average_posting_rate_per_learner']}: {avg_posting_rate:.1f}%\n"
    activity_stats += f" - {t['average_time_spent_per_learner']}: {format_time(avg_time_spent, language)}\n"
    activity_stats += f" - {t['learners_with_consistent_posting']}: {consistent_users / total_users * 100:.1f}%\n"
    activity_stats += f" - {t['learners_showing_improved_engagement']}: {improving_users / total_users * 100:.1f}%\n"

    # Enhanced Action Metrics - now includes all action types
    activity_stats += f"\n{t['action_metrics']}\n"
    total_creates = sum(
        values["total_creates"] for username, values in learner_data.items()
    )
    total_posts = sum(
        values["total_posts"] for username, values in learner_data.items()
    )
    total_replies = sum(
        values["total_replies"] for username, values in learner_data.items()
    )
    total_viewed = sum(
        values["total_viewed"] for username, values in learner_data.items()
    )
    # total_actions = sum(
    #     values["total_actions"] for username, values in learner_data.items()
    # )
    
    activity_stats += f" - {t['average_creates_per_learner']}: {total_creates / total_users:.1f}\n"
    activity_stats += f" - {t['average_posts_per_learner']}: {total_posts / total_users:.1f}\n"
    activity_stats += f" - {t['average_replies_per_learner']}: {total_replies / total_users:.1f}\n"
    activity_stats += f" - {t['average_views_per_learner']}: {total_viewed / total_users:.1f}\n"

    # # Additional aggregate metrics
    # avg_engagement_score = sum(values["engagement_score"] for username, values in learner_data.items()) / total_users
    # avg_disengagement_risk = sum(values["disengagement_risk_score"] for username, values in learner_data.items()) / total_users
    # avg_forum_diversity = sum(values["forum_diversity"] for username, values in learner_data.items()) / total_users
    # activity_stats += "\n**Advanced Metrics** 🔍\n"
    # activity_stats += f" - Average Engagement Score: {avg_engagement_score:.2f}\n"
    # activity_stats += f" - Average Disengagement Risk Score: {avg_disengagement_risk:.2f}\n"
    # activity_stats += f" - Average Forum Diversity: {avg_forum_diversity:.2f}\n"
    
    learner_stats = dict()   
    for username, values in learner_data.items():
        learner_stats[username] = f"{t['learner_engagement_profile']}\n"
        learner_stats[username] += f" - {t['learner_type']}: {t[values['learner_type']]}\n"
        learner_stats[username] += f" - {t['total_sessions']}: {values['total_sessions']}\n"
        learner_stats[username] += f" - {t['posting_sessions']}: {values['posting_sessions']}\n"
        learner_stats[username] += f" - {t['view_only_sessions']}: {values['view_only_sessions']}\n"
        learner_stats[username] += f" - {t['posting_rate']}: {values['posting_rate']:.1f}%\n"
        learner_stats[username] += f" - {t['total_time_spent']}: {format_time(values['total_time_spent'],language)}\n"
        learner_stats[username] += f" - {t['average_time_per_session']}: {format_time(values['avg_time_per_session'],language)}\n"
        # learner_stats[username] += f" - Engagement Score: {values['engagement_score']:.2f}\n"
        # learner_stats[username] += f" - Disengagement Risk Score: {values['disengagement_risk_score']:.2f}\n"
        # learner_stats[username] += f" - Unique Forums: {values['unique_forums']}\n"
        # learner_stats[username] += f" - Forum Diversity: {values['forum_diversity']:.2f}\n"
        learner_stats[username] += f" - {t['consistent_participation']}: {t['yes'] if values['consistent_participation'] else t['no']}\n"
        learner_stats[username] += f" - {t['improving_engagement']}: {t['yes'] if values['improving_engagement'] else t['no']}\n"
        
        # Enhanced Action Breakdown - now includes all action types
        learner_stats[username] += f"\n{t['action_breakdown']}\n"
        learner_stats[username] += f" - {t['created']}: {values['total_creates']}\n"
        learner_stats[username] += f" - {t['uploaded']}: {values['total_uploaded']}\n"
        learner_stats[username] += f" - {t['replied']}: {values['total_replies']}\n"
        learner_stats[username] += f" - {t['posts']}: {values['total_posts']}\n"
        learner_stats[username] += f" - {t['viewed']}: {values['total_viewed']}\n"
                    
        # # Add action frequency breakdown if available
        # if 'action_frequency' in values:
        #     learner_stats[username] += f"\n{t['detailed_action_frequency']}\n"
        #     for action, count in values['action_frequency'].items():
        #         learner_stats[username] += f" - {t[action]}: {count}\n"
        if not module_id:
            learner_stats[username] += f"\n{t['session_details']}\n"
            for i, session in enumerate(values['sessions_details']):
                learner_stats[username] += f" - {t['session']} {i+1}:\n"
                if session['duration'] > 0:
                    learner_stats[username] += f"    * ⏰ {t['start_session']}: {session['start_time'].strftime('%d-%m-%Y %H:%M:%S')}\n"
                    learner_stats[username] += f"    * 🏁 {t['end_session']}: {session['end_time'].strftime('%d-%m-%Y %H:%M:%S')}\n"
                learner_stats[username] += f"    * ⏱️ {t['duration']}: {format_time(session['duration'],language)} {t['min']}\n"
                # Include user interactions
                if session['interactions']:
                    learner_stats[username] += f"    * 📚 {t['associated_learning_resources']}: {', '.join(session['interactions'])}\n"
                
    return learner_stats, learner_data, activity_stats, activity_data