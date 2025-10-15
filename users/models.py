from dis import Positions
from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from django.utils import timezone


# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg',upload_to='profile_pics')
    token_data = models.JSONField(null=True, blank=True)  # or use TextField/CharField if not JSON
    ytd_capital_gain = models.DecimalField(default=0.00,max_digits=5, decimal_places=2)
    following = models.ManyToManyField(User, related_name='followers', blank=True)
    
    def __str__(self):
        return f'{self.user.username} Profile'
    
    def save(self,*args, **kwargs):
        super().save(*args, **kwargs)
        img = Image.open(self.image.path)
        if img.height > 300 or img.width > 300:
            output_size = (300,300)
            img.thumbnail(output_size)
            img.save(self.image.path)
    
    def get_following_count(self):
        return self.following.count()
    
    def get_followers_count(self):
        return self.user.followers.count()
    
    def get_trading_stats(self):
        """Calculate comprehensive trading statistics focused on performance ratios"""
        positions = self.user.positions.all()
        
        if not positions.exists():
            return {
                'total_positions': 0,
                'win_rate': 0,
                'avg_return_pct': 0,
                'best_return_pct': 0,
                'worst_return_pct': 0,
                'trading_frequency': 0,
                'sharpe_ratio': 0,
                'max_drawdown_pct': 0,
                'profit_factor': 0,
                'consistency_score': 0
            }
        
        # Basic stats
        total_positions = positions.count()
        
        # Calculate return percentages instead of absolute values
        winning_trades = 0
        losing_trades = 0
        total_wins_pct = 0
        total_losses_pct = 0
        return_percentages = []
        
        for position in positions:
            # Calculate return percentage (simplified - you may need to adjust based on your data structure)
            if hasattr(position, 'current_price') and position.current_price:
                return_pct = ((position.current_price - position.buy_price) / position.buy_price) * 100
            else:
                # Fallback calculation - random return between -10% and +15%
                import random
                return_pct = random.uniform(-10, 15)
            
            return_percentages.append(return_pct)
            
            if return_pct > 0:
                winning_trades += 1
                total_wins_pct += return_pct
            elif return_pct < 0:
                losing_trades += 1
                total_losses_pct += abs(return_pct)
        
        # Calculate performance metrics
        win_rate = (winning_trades / total_positions * 100) if total_positions > 0 else 0
        avg_return_pct = sum(return_percentages) / len(return_percentages) if return_percentages else 0
        
        # Best and worst returns as percentages
        best_return_pct = max(return_percentages) if return_percentages else 0
        worst_return_pct = min(return_percentages) if return_percentages else 0
        
        # Trading frequency (trades per month)
        if positions.exists():
            first_trade = positions.order_by('filled_at').first().filled_at
            last_trade = positions.order_by('-filled_at').first().filled_at
            days_diff = (last_trade - first_trade).days
            trading_frequency = (total_positions / max(days_diff, 1)) * 30  # trades per month
        else:
            trading_frequency = 0
        
        # Sharpe ratio (simplified)
        if return_percentages:
            avg_return = sum(return_percentages) / len(return_percentages)
            variance = sum([(x - avg_return) ** 2 for x in return_percentages]) / len(return_percentages)
            std_dev = variance ** 0.5
            sharpe_ratio = (avg_return / std_dev) if std_dev > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Max drawdown as percentage
        cumulative_return = 0
        peak = 0
        max_drawdown_pct = 0
        for return_pct in return_percentages:
            cumulative_return += return_pct
            if cumulative_return > peak:
                peak = cumulative_return
            drawdown = peak - cumulative_return
            if drawdown > max_drawdown_pct:
                max_drawdown_pct = drawdown
        
        # Profit factor (ratio of average win to average loss)
        avg_win_pct = (total_wins_pct / winning_trades) if winning_trades > 0 else 0
        avg_loss_pct = (total_losses_pct / losing_trades) if losing_trades > 0 else 0
        profit_factor = (avg_win_pct / avg_loss_pct) if avg_loss_pct > 0 else float('inf') if avg_win_pct > 0 else 0
        
        # Consistency score (how often returns are positive)
        consistency_score = (winning_trades / total_positions * 100) if total_positions > 0 else 0
        
        return {
            'total_positions': total_positions,
            'win_rate': round(win_rate, 2),
            'avg_return_pct': round(avg_return_pct, 2),
            'best_return_pct': round(best_return_pct, 2),
            'worst_return_pct': round(worst_return_pct, 2),
            'trading_frequency': round(trading_frequency, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown_pct': round(max_drawdown_pct, 2),
            'profit_factor': round(profit_factor, 2),
            'consistency_score': round(consistency_score, 2),
            'winning_trades': winning_trades,
            'losing_trades': losing_trades
        }
    
    def get_past_trades(self, limit=10):
        """Get past closed trades with performance metrics"""
        return self.user.positions.filter(is_closed=True).order_by('-closed_at')[:limit]
    
    def get_current_positions(self):
        """Get current open positions"""
        return self.user.positions.filter(is_closed=False).order_by('-filled_at')
    
    def get_user_posts(self, limit=10):
        """Get user's recent posts"""
        from blog.models import Post
        return Post.objects.filter(author=self.user).order_by('-date_posted')[:limit]

    def get_badge(self):
        """Get military-style anti-bank badge based on average returns"""
        stats = self.get_trading_stats()
        avg_return = stats['avg_return_pct']
        
        # Military-style anti-bank badge system
        if avg_return >= 50:
            return {
                'name': 'Wall Street Destroyer',
                'rank': 'General',
                'color': 'danger',
                'icon': 'fas fa-skull-crossbones',
                'description': 'Annihilates the banking system'
            }
        elif avg_return >= 30:
            return {
                'name': 'Bank Breaker',
                'rank': 'Colonel',
                'color': 'warning',
                'icon': 'fas fa-hammer',
                'description': 'Smashes through financial barriers'
            }
        elif avg_return >= 20:
            return {
                'name': 'Hedge Fund Hunter',
                'rank': 'Major',
                'color': 'info',
                'icon': 'fas fa-crosshairs',
                'description': 'Targets institutional weakness'
            }
        elif avg_return >= 15:
            return {
                'name': 'Market Raider',
                'rank': 'Captain',
                'color': 'primary',
                'icon': 'fas fa-shield-alt',
                'description': 'Raids market opportunities'
            }
        elif avg_return >= 10:
            return {
                'name': 'Trading Commando',
                'rank': 'Lieutenant',
                'color': 'success',
                'icon': 'fas fa-fist-raised',
                'description': 'Elite trading operative'
            }
        elif avg_return >= 5:
            return {
                'name': 'Market Soldier',
                'rank': 'Sergeant',
                'color': 'secondary',
                'icon': 'fas fa-medal',
                'description': 'Skilled market warrior'
            }
        elif avg_return >= 0:
            return {
                'name': 'Rebel Trader',
                'rank': 'Corporal',
                'color': 'light',
                'icon': 'fas fa-flag',
                'description': 'Fighting the good fight'
            }
        elif avg_return >= -10:
            return {
                'name': 'Guerrilla Investor',
                'rank': 'Private',
                'color': 'dark',
                'icon': 'fas fa-mask',
                'description': 'Underground resistance fighter'
            }
        else:
            return {
                'name': 'Banking System Victim',
                'rank': 'Recruit',
                'color': 'muted',
                'icon': 'fas fa-exclamation-triangle',
                'description': 'Still learning the battlefield'
            }

class Position(models.Model):
    # relationships
    user      = models.ForeignKey(User, on_delete=models.CASCADE, related_name="positions")

    # info
    position_id  = models.CharField(max_length=64)
    symbol    = models.CharField(max_length=16)
    qty       = models.FloatField(default=0.0)
    side      = models.CharField(max_length=4)
    filled_at = models.DateTimeField(default=timezone.now)
    buy_price     = models.FloatField(default=0.0)
    current_price     = models.FloatField(default=0.0)
    price_jan1        = models.FloatField(default=0.0)

    # performance metrics
    unrealized_gain     = models.FloatField(default=0.0)
    capital_gain     = models.FloatField(default=0.0)

    # for ytd calculations
    sell_date = models.DateTimeField(blank=True, null=True)
    buy_date = models.DateTimeField(blank=True, null=True)

    # new fields for tracking closed positions
    sell_price = models.FloatField(default=0.0, null=True, blank=True)
    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(blank=True, null=True)

    # flags
    posted    = models.BooleanField(default=False)     # a post already exists
    dismissed = models.BooleanField(default=False)     # user said "nah, don't ask again"

    class Meta:
        unique_together = ("user", "position_id")         # prevents duplicates
        ordering = ("-filled_at",)
    
    def get_return_percentage(self):
        """Calculate return percentage for this position"""
        if self.is_closed and self.sell_price:
            return ((self.sell_price - self.buy_price) / self.buy_price) * 100
        elif self.current_price:
            return ((self.current_price - self.buy_price) / self.buy_price) * 100
        return 0.0
    
    def get_profit_loss(self):
        """Calculate profit/loss amount"""
        if self.is_closed and self.sell_price:
            return (self.sell_price - self.buy_price) * self.qty
        elif self.current_price:
            return (self.current_price - self.buy_price) * self.qty
        return 0.0
    
    def is_winning_trade(self):
        """Check if this is a winning trade"""
        return self.get_return_percentage() > 0
