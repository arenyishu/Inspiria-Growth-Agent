import pandas as pd
import random
from datetime import datetime, timedelta

def get_social_daily_data(start_date, end_date):
    """
    Fetches daily aggregate social media data (Followers, Reach, Engagement).
    NOTE: For the Hackathon MVP, since official Meta/LinkedIn API approvals take weeks,
    this module generates realistic simulated data based on typical higher-education growth rates.
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Calculate how many days to generate
        delta = end - start
        days = delta.days + 1
        
        data = []
        
        # Base metrics for a college like Inspiria
        base_followers = 15000
        base_reach = 5000
        
        current_date = start
        for i in range(days):
            # Simulate gradual follower growth with occasional spikes
            daily_new_followers = int(random.normalvariate(15, 5)) 
            if random.random() > 0.95: # 5% chance of a viral post
                daily_new_followers += random.randint(50, 200)
            base_followers += daily_new_followers
            
            # Reach and Engagement
            daily_reach = int(random.normalvariate(base_reach, 800))
            if daily_new_followers > 50:
                daily_reach += random.randint(3000, 8000)
                
            daily_engagement = int(daily_reach * random.uniform(0.04, 0.08)) # 4-8% engagement rate
            
            data.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "total_followers": base_followers,
                "daily_reach": daily_reach,
                "daily_engagement": daily_engagement
            })
            current_date += timedelta(days=1)
            
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error generating social data: {e}")
        return None
