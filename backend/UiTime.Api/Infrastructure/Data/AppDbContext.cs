using Microsoft.EntityFrameworkCore;
using UiTime.Api.Core.Entities;

namespace UiTime.Api.Infrastructure.Data;

public class AppDbContext :  DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<User> Users { get; set; }
    public DbSet<InviteCode> InviteCodes { get; set; }
    public DbSet<Subject> Subjects { get; set; }
    public DbSet<Lesson> Lessons { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);
        
        modelBuilder.Entity<Subject>()
            .Property(s => s.Type)
            .HasConversion<string>();
        
        modelBuilder.Entity<User>()
            .HasIndex(u => u.TelegramId)
            .IsUnique();
        
        modelBuilder.Entity<InviteCode>()
            .HasIndex(i => i.Code)
            .IsUnique();
    }
}