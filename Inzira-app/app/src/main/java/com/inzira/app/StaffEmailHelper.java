package com.inzira.app;

public final class StaffEmailHelper {

    private static final String[] DEFAULT_DOMAINS = {"mifotra.gov.rw"};

    private StaffEmailHelper() {
    }

    public static boolean isStaffEmail(String email) {
        if (email == null || !email.contains("@")) {
            return false;
        }
        String domain = email.trim().toLowerCase().substring(email.indexOf('@') + 1);
        for (String allowed : DEFAULT_DOMAINS) {
            if (domain.equals(allowed)) {
                return true;
            }
        }
        return false;
    }

    public static String requiredDomainHint() {
        return "@" + DEFAULT_DOMAINS[0];
    }
}
