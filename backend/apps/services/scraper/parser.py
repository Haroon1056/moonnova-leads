import re
from urllib.parse import urlparse


class BusinessParser:
    """
    Converts raw Google Maps extracted data into clean Lead model data.

    This parser is designed for international addresses, not only US.
    It supports common formats for:
    - USA
    - Australia
    - Canada
    - UK
    - Pakistan
    - India
    - General city/state/postcode fallback
    """

    # Common country/state/postcode patterns
    AU_STATES = "ACT|NSW|NT|QLD|SA|TAS|VIC|WA"
    US_STATES = (
        "AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|"
        "MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|"
        "VT|VA|WA|WV|WI|WY|DC"
    )
    CA_PROVINCES = "AB|BC|MB|NB|NL|NS|NT|NU|ON|PE|QC|SK|YT"

    def clean(self, value):
        """
        General text cleaner.
        Removes Google Maps icon/private unicode text and extra spacing.
        """

        if value is None:
            return None

        value = str(value).strip()

        if not value:
            return None

        bad_values = [
            "îƒˆ",
            "îƒ‰",
            "îƒŠ",
            "îƒ‹",
            "îƒŒ",
            "îƒŽ",
            "îƒ‘",
            "îƒ’",
            "îƒ“",
            "îƒ•",
            "îƒ–",
            "îƒ˜",
            "îƒ™",
            "îƒš",
            "îƒœ",
            "îƒž",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "\ue0c8",
            "\uf3c5",
            "\uf041",
        ]

        for bad in bad_values:
            value = value.replace(bad, " ")

        # Remove private-use unicode icons and control characters
        value = re.sub(r"[\ue000-\uf8ff]", " ", value)
        value = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", value)

        value = value.replace("\r", " ").replace("\n", " ")
        value = re.sub(r"\s+", " ", value).strip()

        return value if value else None

    def clean_address(self, address):
        """
        Clean address specifically.
        Removes Google labels like Address:, Copy address, Directions, etc.
        """

        address = self.clean(address)

        if not address:
            return None

        address = re.sub(
            r"^\s*(address|copy address|directions|location)\s*[:\-]?\s*",
            "",
            address,
            flags=re.IGNORECASE,
        )

        address = re.sub(r"\s+", " ", address).strip(" ,")

        return address or None

    def clean_phone(self, phone):
        """
        Clean phone number but keep readable formatting.
        """

        phone = self.clean(phone)

        if not phone:
            return None

        phone = (
            phone.replace("Phone:", "")
            .replace("Phone number:", "")
            .replace("Call", "")
            .replace("Copy phone number", "")
            .strip()
        )

        # Keep digits, +, spaces, brackets, dots and dashes
        phone = re.sub(r"[^\d+\-\s().]", "", phone)
        phone = re.sub(r"\s+", " ", phone).strip()

        digits = re.sub(r"\D", "", phone)

        if len(digits) < 7:
            return None

        return phone

    def clean_website(self, website):
        """
        Clean website URL.
        """

        website = self.clean(website)

        if not website:
            return None

        unwanted_values = [
            "website",
            "directions",
            "call",
            "save",
            "share",
            "copy address",
            "copy phone number",
            "send to your phone",
            "open website",
        ]

        if website.lower() in unwanted_values:
            return None

        website = website.replace("Website:", "").strip()

        if website.startswith("http://") or website.startswith("https://"):
            return website

        # example.com
        if "." in website and " " not in website:
            return "https://" + website

        return None

    def clean_rating(self, value):
        """
        Extract rating only, e.g.
        4.8
        4.8 stars
        Rated 4.8 stars
        """

        value = self.clean(value)

        if not value:
            return None

        try:
            match = re.search(r"\b([0-5](?:\.\d+)?)\b", value)

            if match:
                rating = float(match.group(1))

                if 0 <= rating <= 5:
                    return rating

        except Exception:
            return None

        return None

    def clean_count(self, value):
        """
        Extract review/rating count.

        Examples:
        115 reviews
        1,245 reviews
        (115)
        Rated 4.7 stars by 115 people
        """

        if value is None:
            return None

        if isinstance(value, int):
            return value

        value = self.clean(value)

        if not value:
            return None

        try:
            value = value.replace(",", "")

            match = re.search(
                r"(\d+)\s*(?:google\s+)?(reviews?|ratings?|people)",
                value,
                flags=re.IGNORECASE,
            )

            if match:
                return int(match.group(1))

            match = re.search(r"\((\d+)\)", value)

            if match:
                return int(match.group(1))

            # Avoid converting rating only like 4.8 into review count
            if re.fullmatch(r"[0-5](?:\.\d+)?", value):
                return None

            numbers = re.findall(r"\d+", value)

            if numbers:
                return int(numbers[-1])

        except Exception:
            return None

        return None

    def remove_country_from_parts(self, parts):
        """
        Remove final country part when address is comma-separated.
        """

        if not parts:
            return parts

        country_words = [
            "united states",
            "usa",
            "us",
            "australia",
            "canada",
            "united kingdom",
            "uk",
            "england",
            "scotland",
            "wales",
            "india",
            "pakistan",
            "new zealand",
            "ireland",
            "south africa",
            "singapore",
            "uae",
            "united arab emirates",
        ]

        last = parts[-1].strip().lower()

        if last in country_words:
            return parts[:-1]

        return parts

    def extract_from_australia(self, address, parts):
        """
        Australia:
        7A Boskenna Ave, Norwood SA 5067, Australia
        16 Bayvue Cres, Ridgehaven SA 5097, Australia
        """

        pattern = rf"\b(.+?)\s+({self.AU_STATES})\s+(\d{{4}})\b"

        for part in reversed(parts):
            match = re.search(pattern, part, flags=re.IGNORECASE)

            if match:
                city = match.group(1).strip(" ,")
                state = match.group(2).upper()
                pincode = match.group(3)
                return city, state, pincode

        match = re.search(pattern, address, flags=re.IGNORECASE)

        if match:
            city = match.group(1).strip(" ,")
            state = match.group(2).upper()
            pincode = match.group(3)

            # If city captured too much text, take last comma part
            if "," in city:
                city = city.split(",")[-1].strip()

            return city, state, pincode

        return None, None, None

    def extract_from_us(self, address, parts):
        """
        USA:
        115 E 6th St, Austin, TX 78701, United States
        """

        pattern = rf"\b({self.US_STATES})\s+(\d{{5}}(?:-\d{{4}})?)\b"

        for index, part in enumerate(parts):
            match = re.search(pattern, part, flags=re.IGNORECASE)

            if match:
                state = match.group(1).upper()
                pincode = match.group(2)

                city = None

                if index - 1 >= 0:
                    city = parts[index - 1].strip(" ,")

                return city, state, pincode

        match = re.search(pattern, address, flags=re.IGNORECASE)

        if match:
            state = match.group(1).upper()
            pincode = match.group(2)
            return None, state, pincode

        return None, None, None

    def extract_from_canada(self, address, parts):
        """
        Canada:
        123 King St W, Toronto, ON M5V 2T6, Canada
        """

        pattern = rf"\b({self.CA_PROVINCES})\s+([A-Z]\d[A-Z]\s?\d[A-Z]\d)\b"

        for index, part in enumerate(parts):
            match = re.search(pattern, part, flags=re.IGNORECASE)

            if match:
                state = match.group(1).upper()
                pincode = match.group(2).upper()

                city = None

                if index - 1 >= 0:
                    city = parts[index - 1].strip(" ,")

                return city, state, pincode

        match = re.search(pattern, address, flags=re.IGNORECASE)

        if match:
            state = match.group(1).upper()
            pincode = match.group(2).upper()
            return None, state, pincode

        return None, None, None

    def extract_from_uk(self, address, parts):
        """
        UK:
        10 Downing St, London SW1A 2AA, United Kingdom
        221B Baker St, London NW1 6XE, UK
        """

        postcode_pattern = r"\b([A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2})\b"

        for part in reversed(parts):
            match = re.search(postcode_pattern, part, flags=re.IGNORECASE)

            if match:
                pincode = match.group(1).upper()
                before = part[: match.start()].strip(" ,")

                city = before if before else None
                state = None

                if not city and len(parts) >= 2:
                    city = parts[-2].strip(" ,")

                return city, state, pincode

        match = re.search(postcode_pattern, address, flags=re.IGNORECASE)

        if match:
            pincode = match.group(1).upper()
            return None, None, pincode

        return None, None, None

    def extract_from_india_pakistan_general(self, address, parts):
        """
        India / Pakistan / general South Asian style:
        Mumbai, Maharashtra 400001, India
        Faisalabad, Punjab 38000, Pakistan
        Lahore, Punjab, 54000, Pakistan
        """

        # State + 5/6 digit postal code
        pattern = r"\b([A-Za-z][A-Za-z\s.&'-]{2,})\s+(\d{5,6})\b"

        for index, part in enumerate(parts):
            match = re.search(pattern, part)

            if match:
                state = match.group(1).strip()
                pincode = match.group(2)

                city = None

                if index - 1 >= 0:
                    city = parts[index - 1].strip(" ,")

                return city, state, pincode

        # If separate postal code part exists
        for index, part in enumerate(parts):
            if re.fullmatch(r"\d{5,6}", part.strip()):
                pincode = part.strip()

                city = parts[index - 2].strip(" ,") if index - 2 >= 0 else None
                state = parts[index - 1].strip(" ,") if index - 1 >= 0 else None

                return city, state, pincode

        return None, None, None

    def extract_general(self, address, parts):
        """
        General fallback:
        Tries to detect postcode and infer city/state from comma parts.
        """

        city = None
        state = None
        pincode = None

        cleaned_parts = self.remove_country_from_parts(parts)

        # Generic postal code: 4 to 10 chars, supports letters/digits
        postcode_match = re.search(
            r"\b([A-Z]?\d[A-Z\d]?\s?\d[A-Z]{0,3}|\d{4,6}(?:-\d{4})?)\b",
            address,
            flags=re.IGNORECASE,
        )

        if postcode_match:
            pincode = postcode_match.group(1).upper()

        # If comma-separated, use the last parts
        if len(cleaned_parts) >= 3:
            # Usually: Street, City, State/Postcode
            city = cleaned_parts[-2].strip(" ,")

            last = cleaned_parts[-1].strip(" ,")

            # Try state from last part before postcode
            if pincode and pincode in last:
                possible_state = last.replace(pincode, "").strip(" ,")
                state = possible_state or None
            else:
                state = last or None

        elif len(cleaned_parts) == 2:
            # Usually: Street, City State Postcode
            last = cleaned_parts[-1].strip(" ,")

            if pincode and pincode in last:
                before_pin = last.replace(pincode, "").strip(" ,")

                # Split into words; last word may be state, earlier words city
                words = before_pin.split()

                if len(words) >= 2:
                    city = " ".join(words[:-1])
                    state = words[-1]
                else:
                    city = before_pin or None
            else:
                city = last

        return city, state, pincode

    def extract_city_state_zip(self, address):
        """
        Main international address parser.
        Returns: city, state, pincode
        """

        city = None
        state = None
        pincode = None

        address = self.clean_address(address)

        if not address:
            return city, state, pincode

        try:
            parts = [part.strip() for part in address.split(",") if part.strip()]
            parts = self.remove_country_from_parts(parts)

            extractors = [
                self.extract_from_australia,
                self.extract_from_us,
                self.extract_from_canada,
                self.extract_from_uk,
                self.extract_from_india_pakistan_general,
                self.extract_general,
            ]

            for extractor in extractors:
                city, state, pincode = extractor(address, parts)

                if city or state or pincode:
                    return (
                        self.clean(city),
                        self.clean(state),
                        self.clean(pincode),
                    )

        except Exception:
            pass

        return city, state, pincode

    def parse(self, raw, keyword=None, location=None):
        """
        Main parser used by engine.py
        """

        address = self.clean_address(raw.get("address"))

        city = self.clean(raw.get("city"))
        state = self.clean(raw.get("state"))
        pincode = self.clean(raw.get("pincode"))

        parsed_city, parsed_state, parsed_pincode = self.extract_city_state_zip(address)

        if not city:
            city = parsed_city

        if not state:
            state = parsed_state

        if not pincode:
            pincode = parsed_pincode

        rating_count = self.clean_count(raw.get("rating_count"))
        review_count = self.clean_count(raw.get("review_count"))

        if not review_count and rating_count:
            review_count = rating_count

        if not rating_count and review_count:
            rating_count = review_count

        return {
            "keyword": self.clean(keyword),
            "location": self.clean(location),

            "name": self.clean(raw.get("name")),
            "category": self.clean(raw.get("category")),

            "website": self.clean_website(raw.get("website")),
            "phone": self.clean_phone(raw.get("phone")),

            "address": address,
            "city": city,
            "state": state,
            "pincode": pincode,

            "rating": self.clean_rating(raw.get("rating")),
            "rating_count": rating_count,
            "review_count": review_count,

            "map_link": self.clean(raw.get("map_link")),

            "email_1": None,
            "email_2": None,
            "email_3": None,
        }

    def is_valid(self, data):
        """
        A lead is valid only when business name exists
        and at least phone, website, or address exists.
        """

        if not data:
            return False

        name = data.get("name")

        if not name:
            return False

        bad_names = [
            "results",
            "google maps",
            "maps",
            "directions",
            "website",
            "call",
            "save",
            "share",
            "menu",
        ]

        if name.lower().strip() in bad_names:
            return False

        return bool(
            data.get("phone")
            or data.get("website")
            or data.get("address")
        )