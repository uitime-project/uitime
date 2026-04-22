using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using UiTime.Api.Core.DTOs;
using UiTime.Api.Core.Entities;
using UiTime.Api.Infrastructure.Data;
using UiTime.Api.Infrastructure.Services;

namespace UiTime.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
[AllowAnonymous]
public class ScheduleController : ControllerBase
{
    public readonly AppDbContext _context;
    public readonly IScheduleParserService _parserService;

    public ScheduleController(AppDbContext dbContext, IScheduleParserService scheduleParserService)
    {
        _context = dbContext;
        _parserService = scheduleParserService;
    }
    
    [HttpPost("upload")]
    public async Task<IActionResult> UploadSchedule(IFormFile file)
    {
        if (file == null || file.Length == 0)
            return BadRequest("File is empty or not provided.");
        
        var telegramIdString = User.FindFirst(ClaimTypes.NameIdentifier)?.Value 
                               ?? User.FindFirst("sub")?.Value;

        if (!long.TryParse(telegramIdString, out var telegramId))
            return Unauthorized("Invalid token claims. Cannot find TelegramId.");
        
        var user = await _context.Users.FirstOrDefaultAsync(u => u.TelegramId == telegramId);
        if (user == null)
            return NotFound("User not found in database.");
        
        using var stream = file.OpenReadStream();
        var parsedLessons = _parserService.ParseSchedule(stream).ToList();

        if (!parsedLessons.Any())
            return Ok(new { Message = "No lessons found in the file." });
        
        var existingSubjects = await _context.Subjects.ToListAsync();
        var newLessons = new List<Lesson>();

        foreach (var parsed in parsedLessons)
        {
            var subject = existingSubjects.FirstOrDefault(s => 
                s.Name == parsed.SubjectNameRaw && s.Type == parsed.Type);

            if (subject == null)
            {
                subject = new Subject
                {
                    Name = parsed.SubjectNameRaw,
                    Type = parsed.Type,
                    HasExam = false
                };
                _context.Subjects.Add(subject);
                existingSubjects.Add(subject);
            }
            
            newLessons.Add(new Lesson
            {
                UserId = user.Id,
                Subject = subject,
                StartTime = parsed.StartTime,
                EndTime = parsed.EndTime,
                Location = parsed.Location,
                OnlineLink = parsed.OnlineLink
            });
        }
        
        var existingUserLessons = await _context.Lessons
            .Where(l => l.UserId == user.Id)
            .ToListAsync();
        
        _context.Lessons.RemoveRange(existingUserLessons);
        
        _context.Lessons.AddRange(newLessons);
        await _context.SaveChangesAsync();

        return Ok(new { Message = $"Successfully uploaded {newLessons.Count} lessons for user {user.Username}." });
    }
    
   [HttpGet("today")]
    public async Task<ActionResult<IEnumerable<LessonDto>>> GetTodaySchedule()
    {
        var telegramIdString = User.FindFirst(ClaimTypes.NameIdentifier)?.Value 
                               ?? User.FindFirst("sub")?.Value;
        
        if (!long.TryParse(telegramIdString, out long telegramId))
        {
            return Unauthorized("Invalid token claims. Cannot find TelegramId."); 
        }
        
        var startOfToday = DateTime.UtcNow.Date;
        var startOfTomorrow = startOfToday.AddDays(1);
        
        var lessons = await _context.Lessons
            .Where(l => l.User.TelegramId == telegramId 
                        && l.StartTime >= startOfToday 
                        && l.StartTime < startOfTomorrow)
            .OrderBy(l => l.StartTime)
            .Select(l => new LessonDto(
                l.Id,
                l.Subject.Name,  
                l.Subject.Type,
                l.StartTime,
                l.EndTime,
                l.Location,
                l.OnlineLink
            ))
            .ToListAsync();

        return Ok(lessons);
    }

    [HttpGet("tomorrow")]
    public async Task<ActionResult<IEnumerable<LessonDto>>> GetTomorrowSchedule()
    {
        var telegramIdString = User.FindFirst(ClaimTypes.NameIdentifier)?.Value 
                               ?? User.FindFirst("sub")?.Value;
        
        if (!long.TryParse(telegramIdString, out long telegramId))
        {
            return Unauthorized("Invalid token claims. Cannot find TelegramId."); 
        }
        
        var startOfTomorrow = DateTime.UtcNow.Date.AddDays(1);
        var startOfDayAfterTomorrow = startOfTomorrow.AddDays(1);
        
        var lessons = await _context.Lessons
            .Where(l => l.User.TelegramId == telegramId 
                        && l.StartTime >= startOfTomorrow 
                        && l.StartTime < startOfDayAfterTomorrow)
            .OrderBy(l => l.StartTime)
            .Select(l => new LessonDto(  
                l.Id,
                l.Subject.Name,     
                l.Subject.Type,
                l.StartTime,
                l.EndTime,
                l.Location,
                l.OnlineLink
            ))
            .ToListAsync();

        return Ok(lessons);
    }
    
    [HttpGet("date/{date}")]
    public async Task<ActionResult<IEnumerable<LessonDto>>> GetScheduleByDate([FromRoute] DateTime date)
    {
        var telegramIdString = User.FindFirst(ClaimTypes.NameIdentifier)?.Value 
                               ?? User.FindFirst("sub")?.Value;
        
        if (!long.TryParse(telegramIdString, out long telegramId))
        {
            return Unauthorized("Invalid token claims. Cannot find TelegramId."); 
        }
        
        var startOfDay = date.Date; 
        var endOfDay = startOfDay.AddDays(1);
        
        var lessons = await _context.Lessons
            .Where(l => l.User.TelegramId == telegramId 
                        && l.StartTime >= startOfDay 
                        && l.StartTime < endOfDay)
            .OrderBy(l => l.StartTime)
            .Select(l => new LessonDto(  
                l.Id,
                l.Subject.Name,     
                l.Subject.Type,
                l.StartTime,
                l.EndTime,
                l.Location,
                l.OnlineLink
            ))
            .ToListAsync();

        return Ok(lessons);
    }
    
    [HttpGet("nearest")]
    public async Task<ActionResult<IEnumerable<LessonDto>>> GetNearestDaySchedule()
    {
        var telegramIdString = User.FindFirst(ClaimTypes.NameIdentifier)?.Value 
                               ?? User.FindFirst("sub")?.Value;
        
        if (!long.TryParse(telegramIdString, out long telegramId))
        {
            return Unauthorized("Invalid token claims. Cannot find TelegramId."); 
        }

        var now = DateTime.UtcNow;
        
        var nearestLesson = await _context.Lessons
            .Where(l => l.User.TelegramId == telegramId && l.StartTime >= now)
            .OrderBy(l => l.StartTime)
            .FirstOrDefaultAsync();
        
        if (nearestLesson == null)
        {
            return Ok(new List<LessonDto>());
        }
        
        var startOfDay = nearestLesson.StartTime.Date;
        var endOfDay = startOfDay.AddDays(1);
        
        var lessons = await _context.Lessons
            .Where(l => l.User.TelegramId == telegramId 
                        && l.StartTime >= startOfDay 
                        && l.StartTime < endOfDay)
            .OrderBy(l => l.StartTime)
            .Select(l => new LessonDto(  
                l.Id,
                l.Subject.Name,     
                l.Subject.Type,
                l.StartTime,
                l.EndTime,
                l.Location,
                l.OnlineLink
            ))
            .ToListAsync();

        return Ok(lessons);
    }
}