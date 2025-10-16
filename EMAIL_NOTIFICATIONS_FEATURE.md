# Email Notifications Feature

## Overview
Users can now subscribe to receive email notifications when traders they follow make new posts.

## Features

### 1. **Notification Bell on User Profiles**
- Visible only when you're following a user
- Shows two states:
  - **OFF** (gray bell icon): "Get Email Notifications"
  - **ON** (yellow bell icon): "Notifications ON"

### 2. **Requirements**
- You must follow a user before enabling email notifications
- You cannot enable notifications for yourself
- The system uses your Django email configuration (Gmail SMTP)

### 3. **How It Works**

#### For Users:
1. Go to any user's profile
2. Click the "Follow" button (if not already following)
3. Click "Get Email Notifications" button
4. You'll now receive emails when they post

#### For Post Authors:
When you create a new post:
- All users who enabled notifications for you will receive an email
- Email contains:
  - Your username
  - Stock symbol and side (BUY/SELL)
  - Post excerpt (first 200 characters)
  - Link to the full post
  - Instructions to manage notifications

### 4. **Email Content**
```
Subject: New post from [username] on MarketMaven

Hello [subscriber_name],

[author_username] just posted about [SYMBOL] ([BUY/SELL]).

[Post content preview...]

View the full post here: [link]

---
To manage your notification settings, visit your profile on MarketMaven.

This email was sent because you enabled email notifications for [author]'s posts.
```

## Implementation Details

### Database Schema
**New Field in Profile Model:**
```python
email_notifications = models.ManyToManyField(User, related_name='email_subscribers', blank=True)
```

This creates a many-to-many relationship allowing users to subscribe to multiple traders' notifications.

### Files Modified

1. **users/models.py**
   - Added `email_notifications` field to Profile
   - Added helper methods:
     - `has_email_notifications_for(user)` - Check subscription status
     - `toggle_email_notifications(user)` - Toggle subscription

2. **users/views.py**
   - Added `toggle_email_notifications()` view
   - Updated `user_profile()` to pass notification status to template

3. **users/templates/users/user_profile.html**
   - Added notification bell button with conditional states

4. **blog/views.py**
   - Modified `PostCreateView.form_valid()` to send emails
   - Added `send_email_notifications()` method

5. **tutorial/urls.py**
   - Added URL route: `toggle-notifications/<username>/`

### URL Routes
- `POST /toggle-notifications/<username>/` - Toggle email notifications

### Permissions
- Must be authenticated
- Must follow the user
- Cannot subscribe to own posts

## Testing

### Test Email Notifications:
1. Configure your email settings in `.env`:
   ```
   APP_EMAIL=your-email@gmail.com
   APP_PASSWORD=your-app-password
   ```

2. Create two test accounts
3. Account A follows Account B
4. Account A clicks "Get Email Notifications" on B's profile
5. Account B creates a post
6. Account A should receive an email

### Verify in Admin:
- Go to `/admin/users/profile/`
- Select a profile
- Check "Email notifications" field to see subscriptions

## Error Handling
- Emails sent with `fail_silently=True` - won't crash if email fails
- Errors logged to console
- Post creation succeeds even if email fails

## Future Enhancements

### Possible Additions:
1. **Notification Preferences Page**
   - View all subscriptions in one place
   - Bulk manage notifications

2. **Email Templates**
   - HTML email templates with branding
   - Better formatting

3. **Digest Emails**
   - Daily/weekly summary instead of immediate emails
   - Reduce email fatigue

4. **Notification Types**
   - Choose to be notified for specific stocks only
   - Filter by trade type (BUY vs SELL)

5. **Email Verification**
   - Require email confirmation before sending notifications
   - Unsubscribe links

6. **Rate Limiting**
   - Prevent spam if user posts too frequently
   - Queue system for batch sending

## Security Considerations
- Email addresses not exposed to other users
- Unsubscribe requires authentication
- No email validation on toggle (assumes Django user emails are valid)

## Performance Notes
- Emails sent synchronously during post creation
- For many subscribers, consider:
  - Async task queue (Celery)
  - Background workers
  - Batch email sending

---

**Implementation Status**: ✅ COMPLETE
**Last Updated**: October 16, 2025
**Migration**: 0022_profile_email_notifications_delete_notification.py

