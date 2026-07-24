package com.inzira.app;

import java.util.List;

public class YouthProfileRequest {
    public String name;
    public String district;
    public String age;
    public String education;
    public List<String> skills;
    public List<String> interests;

    public YouthProfileRequest(String name, String district, String age,
                               String education, List<String> skills, List<String> interests) {
        this.name = name;
        this.district = district;
        this.age = age;
        this.education = education;
        this.skills = skills;
        this.interests = interests;
    }
}
