#!/usr/bin/env python3
"""
Simple script to delete all Posts, Photos, and Reels from a Facebook Page.
"""

import os
import sys
import requests

def check_env_vars():
    """Check for required environment variables."""
    token = os.getenv('FB_PAGE_TOKEN')
    page_id = os.getenv('FB_PAGE_ID')
    
    if not token or not page_id:
        print("❌ Error: Missing environment variables.")
        print("Please set FB_PAGE_TOKEN and FB_PAGE_ID.")
        sys.exit(1)
    
    return token, page_id

def make_api_request(url, method='GET', token=None):
    """Make a simple API request."""
    params = {'access_token': token} if token else {}
    try:
        if method.upper() == 'DELETE':
            response = requests.delete(url, params=params)
        else:  # GET
            response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        print(f"   ⚠️  API Error: {e}")
        return None

def delete_all_content():
    """Main function to delete all page content."""
    token, page_id = check_env_vars()
    base_url = f"https://graph.facebook.com/v19.0"
    
    print(f"🗑️  Starting deletion for Page ID: {page_id}")
    print("=" * 50)
    
    # 1. Delete Posts from the feed
    print("\n1. Deleting Posts...")
    posts_url = f"{base_url}/{page_id}/feed"
    delete_content_by_type(posts_url, token, "post")
    
    # 2. Delete Uploaded Photos
    print("\n2. Deleting Uploaded Photos...")
    photos_url = f"{base_url}/{page_id}/photos?type=uploaded"
    delete_content_by_type(photos_url, token, "photo")
    
    # 3. Delete Reels
    print("\n3. Deleting Reels...")
    reels_url = f"{base_url}/{page_id}/videos?type=uploaded"
    delete_content_by_type(reels_url, token, "reel")
    
    print("=" * 50)
    print("✅ Deletion process completed.")
    print("Note: Some content like shared posts or ads may not be deleted.")

def delete_content_by_type(content_url, token, content_type):
    """Fetch and delete content from a specific API endpoint."""
    delete_count = 0
    error_count = 0
    url = content_url
    
    while url:
        data = make_api_request(url, 'GET', token)
        
        if not data or 'data' not in data:
            print(f"   No more {content_type}s found or error in response.")
            break
        
        items = data.get('data', [])
        
        for item in items:
            item_id = item.get('id')
            if item_id:
                delete_url = f"https://graph.facebook.com/v19.0/{item_id}"
                result = make_api_request(delete_url, 'DELETE', token)
                
                if result and result.get('success'):
                    print(f"   ✅ Deleted {content_type}: {item_id[:15]}...")
                    delete_count += 1
                else:
                    print(f"   ❌ Failed to delete {content_type}: {item_id[:15]}...")
                    error_count += 1
        
        # Check for next page
        paging = data.get('paging', {})
        url = paging.get('next')
    
    print(f"   Summary: {delete_count} deleted, {error_count} errors.")

if __name__ == "__main__":
    # Confirmation before running
    print("⚠️  WARNING: This will permanently delete content from your Facebook Page.")
    print("Deleted content CANNOT be recovered.")
    
    response = input("Type 'DELETE' to confirm and continue: ")
    
    if response.strip().upper() == 'DELETE':
        delete_all_content()
    else:
        print("Operation cancelled.")