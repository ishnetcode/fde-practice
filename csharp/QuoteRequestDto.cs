public enum CoverType { Comprehensive, ThirdPartyFireTheft, ThirdParty }

public class DriverDto
{
    [Required, StringLength(100, MinimumLength = 1)]
    public string FullName { get; set; }

    [Range(17, 99)]
    public int Age { get; set; }

    public int? YearsNoClaims { get; set; }   // optional
}

public class QuoteRequestDto
{
    [Required, StringLength(20, MinimumLength = 2)]
    public string PolicyId { get; set; }

    [Required]
    public CoverType Cover { get; set; }

    [Range(0.01, double.MaxValue)]
    public decimal Premium { get; set; }

    public DateTime StartDate { get; set; }   // must accept UK dates too

    [MinLength(1)]
    public List<DriverDto> Drivers { get; set; }
}