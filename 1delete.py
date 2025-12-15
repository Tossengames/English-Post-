#!/usr/bin/env python3
"""
Simple script to delete all Posts, Photos, and Reels from a Facebook Page.
Designed to run in GitHub Actions without manual input.
"""

import os
import sys
import requests
import time

def check_env_vars():
    """Check for required environment variables."""
    token = os.getenv('FB_PAGE_TOKEN')
    page_id = os.getenv('FB_PAGE_ID')
    
    if not token or not page_id:
        print("❌ Error: Missing environment variables.")
        print("Please set FB_PAGE_TOKEN and FB_PAGE_ID.")
        sys.exit(1)
    
    return token, page_id

def make_api_request(url, method='GET', token=None, params=None):
    """Make a simple API request to the Facebook Graph API."""
    if params is None:
        params = {}
    if token:
        params['access_token'] = token

    try:
        if method.upper() == 'DELETE':
            response = requests.delete(url, params=params)
        else:  # GET
            response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️  API Request Error: {e}")
        return None

def delete_content_by_type(content_url, token, content_type):
    """Fetch and delete content from a specific API endpoint."""
    delete_count = 0
    error_count = 0
    url = content_url
    
    print(f"   Starting deletion for {content_type}s...")
    
    while url:
        # Fetch a page of content
        data = make_api_request(url, 'GET', token)
        
        if not data or 'data' not in data:
            print(f"   No more {content_type}s found or error in response.")
            break
        
        items = data.get('data', [])
        
        if not items:
            print(f"   No {content_type}s in this batch.")
            break
        
        # Delete each item in the current batch
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
                # Small delay to be respectful of API rate limits
                time.sleep(0.5)
        
        # Check for next page
        paging = data.get('paging', {})
        url = paging.get('next')
    
    print(f"   Summary: {delete_count} deleted, {error_count} errors for {content_type}s.")
    return delete_count, error_count

def delete_all_content():
    """Main function to delete all page content."""
    token, page_id = check_env_vars()
    base_url = f"https://graph.facebook.com/v19.0"
    
    print(f"🗑️  Starting bulk deletion for Page ID: {page_id}")
    print("=" * 50)
    
    total_deleted = 0
    total_errors = 0
    
    # 1. Delete Posts from the feed [citation:1]
    print("\n1. Deleting Posts...")
    posts_url = f"{base_url}/{page_id}/feed"
    deleted, errors = delete_content_by_type(posts_url, token, "post")
    total_deleted += deleted
    total_errors += errors
    
    # 2. Delete Uploaded Photos [citation:1]
    print("\n2. Deleting Uploaded Photos...")
    photos_url = f"{base_url}/{page_id}/photos"
    deleted, errors = delete_content_by_type(photos_url, token, "photo")
    total_deleted += deleted
    total_errors += errors
    
    # 3. Delete Videos/Reels [citation:1]
    print("\n3. Deleting Videos/Reels...")
    videos_url = f"{base_url}/{page_id}/videos"
    deleted, errors = delete_content_by_type(videos_url, token, "video")
    total_deleted += deleted
    total_errors += errors
    
    print("=" * 50)
    print("✅ Deletion process completed.")
    print(f"Total: {total_deleted} items deleted, {total_errors} errors.")

if __name__ == "__main__":
    # This script is designed for automated environments like GitHub Actions.
    # It runs immediately without a confirmation prompt.
    print("⚠️  WARNING: This will permanently delete content from your Facebook Page.")
    print("Deleted content CANNOT be recovered.")
    print("Script is configured for automated run. Starting in 2 seconds...")
    time.sleep(2)
    
    delete_all_content()