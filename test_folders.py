#!/usr/bin/env python3
"""
Comprehensive Dropbox app diagnostics
"""
import os
import dropbox

def test_dropbox_comprehensive():
    token = os.getenv('DROPBOX_ACCESS_TOKEN')
    
    if not token:
        print("❌ DROPBOX_ACCESS_TOKEN environment variable not found")
        return False
    
    print(f"✅ Found token: {token[:10]}...{token[-4:]}")
    
    try:
        dbx = dropbox.Dropbox(token)
        
        # Get account info
        account = dbx.users_get_current_account()
        print(f"✅ Connected to: {account.email}")
        
        # Check what type of app this is
        print("\n🔍 Testing app scope...")
        
        # Test root folder access
        try:
            root_result = dbx.files_list_folder('', limit=10)
            print(f"📁 Root folder ('') access: SUCCESS - {len(root_result.entries)} items")
            
            if len(root_result.entries) > 0:
                print("   Files found in root:")
                for entry in root_result.entries[:5]:
                    if isinstance(entry, dropbox.files.FileMetadata):
                        print(f"     📄 {entry.name} ({entry.size} bytes)")
                    else:
                        print(f"     📁 {entry.name}/")
            else:
                print("   Root folder is empty")
                
        except dropbox.exceptions.ApiError as e:
            print(f"📁 Root folder ('') access: FAILED - {e}")
        
        # Test explicit app folder access
        try:
            app_result = dbx.files_list_folder('/Apps/cindytest', limit=10)
            print(f"📁 App folder ('/Apps/cindytest') access: SUCCESS - {len(app_result.entries)} items")
            
            if len(app_result.entries) > 0:
                print("   Files found in app folder:")
                for entry in app_result.entries[:5]:
                    if isinstance(entry, dropbox.files.FileMetadata):
                        print(f"     📄 {entry.name} ({entry.size} bytes)")
                    else:
                        print(f"     📁 {entry.name}/")
                        
        except dropbox.exceptions.ApiError as e:
            print(f"📁 App folder ('/Apps/cindytest') access: FAILED - {e}")
        
        # Test if we can access other areas (this will fail for app folder apps)
        try:
            other_result = dbx.files_list_folder('/Documents', limit=5)
            print(f"📁 Documents folder access: SUCCESS - Full Dropbox app")
        except dropbox.exceptions.ApiError as e:
            print(f"📁 Documents folder access: FAILED - App Folder app (this is expected)")
        
        # Get space usage to understand app type
        try:
            space_usage = dbx.users_get_space_usage()
            print(f"💾 Total space used: {space_usage.used} bytes")
        except Exception as e:
            print(f"💾 Space usage: Could not retrieve ({e})")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_dropbox_comprehensive()
