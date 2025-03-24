from app.services.cloud_lens_helper import filter_source_by_domain


def test_filter_by_domain_no_domains():
    mock_lens_matched_images = [
        {
            "title": "Manbusiness hi-res stock photography and images - Alamy from Alamy",
            "pageUrl": "https://MOCK.MOCK_DOMAIN.alamy.com/stock-photo/manbusiness.html",
            "imageUrl": "https://MOCK.encrypted-tbn1.gstatic.com/images?q=tbn:ANd9GcRHaIbhYx2XJ1HvuIQocp6lkCA-lDyRvjUNdhTzFe25_463lFoj",
            "source": "Alamy",
        },
        {
            "title": "Mid adult black man smiling to camera in an open - stock photo 281918 | Crushpixel from Crushpixel",
            "pageUrl": "https://MOCK.MOCK_DOMAIN.crushpixel.com/stock-photo/mid-adult-black-man-smiling-281918.html",
            "imageUrl": "https://MOCK.encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcRT_tcyHMWDFLqXKL3uhRJSv0KaU6lu1Bbj-LzsCAlhnywxNsD6",
            "source": "Crushpixel",
        },
        {
            "title": "Stock Photo: Smile, happy and motivation for business man, manager and leader alone in city, town or downtown. Portrait of excited corporate worker,  $30.00* from pixtastock.com",
            "pageUrl": "https://MOCK.MOCK_DOMAIN.pixtastock.com/photo/110350455",
            "imageUrl": "https://MOCK.encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTxoDp5b2Pt7506BnF7sf4uVN-t0RC4UTW5loOYjl7ZG3K1g5NQ",
            "source": "",
        },
        {
            "title": "A Young Man In A Business Suit With A Blue Shirt And Red Tie On A City Street High-Res Stock Photo - Getty Images from Getty Images UK",
            "pageUrl": "https://MOCK.MOCK_DOMAIN.gettyimages.ae/detail/photo/young-man-in-a-business-suit-with-a-blue-shirt-and-royalty-free-image/464720771",
            "imageUrl": "https://MOCK.encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSMOQAx4QxkEhwahQ8yjZC8E3cECPy44xqL4uHj57zsShXT9y6h",
            "source": "Getty Images UK",
        },
        {
            "title": "Black man, business and face, smile outdoor and professional mindset with confidence in city. Happy $5.00* from PhotoDune",
            "pageUrl": "https://MOCK.photodune.net/item/black-man-business-and-face-smile-outdoor-and-professional-mindset-with-confidence-in-city-happy/48566148",
            "imageUrl": "https://MOCK.encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcS2Bes8zIx4kZvXr7-X38TUNgkLqsjAXVIaQ6DxzGOE4dv8acyr",
            "source": "",
        },
        {
            "title": "Stock Illustration: attractive middle aged african american man on blue background. handsomeTV presenter in studio on popular channel. live stream  $30.00* from pixtastock.com",
            "pageUrl": "https://MOCK.MOCK_DOMAIN.pixtastock.com/illustration/107748603",
            "imageUrl": "https://MOCK.encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcSh52McM6NjMnWlnqf4f3OloFvyZJ6MJlrKmQ3TmAKg77Vew1iA",
            "source": "",
        },
        {
            "title": "Portrait of handsome African businessman wearing suit and tie while smiling at rooftop park $5.00* from PhotoDune",
            "pageUrl": "https://MOCK.photodune.net/item/portrait-of-handsome-african-businessman-wearing-suit-and-tie-while-smiling-at-rooftop-park/34324771",
            "imageUrl": "https://MOCK.encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcQYDPBn9WeWMFJ58YBGhLj8qXr2WmFvC6E3BKT69re7IxDa4lFB",
            "source": "",
        }
    ]
    filtered = filter_source_by_domain(mock_lens_matched_images, [])

    assert filtered[0]["source"] == "Alamy"
    assert filtered[1]["source"] == "Crushpixel"
    assert filtered[2]["source"] == ""
    assert filtered[3]["source"] == "Getty Images UK"
    assert filtered[4]["source"] == ""
    assert filtered[5]["source"] == ""
    assert filtered[6]["source"] == ""


def test_filter_by_domain_with_one_domain():
    mock_lens_matched_images = [
        {
            "title": "Manbusiness hi-res stock photography and images - Alamy from Alamy",
            "pageUrl": "https://MOCK.MOCK_DOMAIN.alamy.com/stock-photo/manbusiness.html",
            "imageUrl": "https://MOCK.encrypted-tbn1.gstatic.com/images?q=tbn:ANd9GcRHaIbhYx2XJ1HvuIQocp6lkCA-lDyRvjUNdhTzFe25_463lFoj",
            "source": "MOCK_DOMAIN",
        },
        {
            "title": "Mid adult black man smiling to camera in an open - stock photo 281918 | Crushpixel from Crushpixel",
            "pageUrl": "https://MOCK.NOOOOOOOOOO.crushpixel.com/stock-photo/mid-adult-black-man-smiling-281918.html",
            "imageUrl": "https://MOCK.encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcRT_tcyHMWDFLqXKL3uhRJSv0KaU6lu1Bbj-LzsCAlhnywxNsD6",
            "source": "NO-Crushpixel",
        },
        {
            "title": "Stock Photo: Smile, happy and motivation for business man, manager and leader alone in city, town or downtown. Portrait of excited corporate worker,  $30.00* from pixtastock.com",
            "pageUrl": "https://MOCK.MOCK_DOMAIN.pixtastock.com/photo/110350455",
            "imageUrl": "https://MOCK.encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTxoDp5b2Pt7506BnF7sf4uVN-t0RC4UTW5loOYjl7ZG3K1g5NQ",
            "source": "mock_domain",
        },
        {
            "title": "A Young Man In A Business Suit With A Blue Shirt And Red Tie On A City Street High-Res Stock Photo - Getty Images from Getty Images UK",
            "pageUrl": "https://MOCK.MOCK_DOMAIN.gettyimages.ae/detail/photo/young-man-in-a-business-suit-with-a-blue-shirt-and-royalty-free-image/464720771",
            "imageUrl": "https://MOCK.encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSMOQAx4QxkEhwahQ8yjZC8E3cECPy44xqL4uHj57zsShXT9y6h",
            "source": "MOCK_domain",
        },
        {
            "title": "Black man, business and face, smile outdoor and professional mindset with confidence in city. Happy $5.00* from PhotoDune",
            "pageUrl": "https://MOCK.photodune.net/item/black-man-business-and-face-smile-outdoor-and-professional-mindset-with-confidence-in-city-happy/48566148",
            "imageUrl": "https://MOCK.encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcS2Bes8zIx4kZvXr7-X38TUNgkLqsjAXVIaQ6DxzGOE4dv8acyr",
            "source": "NO",
        },
        {
            "title": "Stock Illustration: attractive middle aged african american man on blue background. handsomeTV presenter in studio on popular channel. live stream  $30.00* from pixtastock.com",
            "pageUrl": "https://MOCK.pixtastock.com/illustration/107748603",
            "imageUrl": "https://MOCK.MOCK_DOMAIN.encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcSh52McM6NjMnWlnqf4f3OloFvyZJ6MJlrKmQ3TmAKg77Vew1iA",
            "source": "MOCK_DOMAIN",
        },
        {
            "title": "Portrait of handsome African businessman wearing suit and tie while smiling at rooftop park $5.00* from PhotoDune",
            "pageUrl": "https://MOCK.photodune.net/item/portrait-of-handsome-african-businessman-wearing-suit-and-tie-while-smiling-at-rooftop-park/34324771",
            "imageUrl": "https://MOCK.encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcQYDPBn9WeWMFJ58YBGhLj8qXr2WmFvC6E3BKT69re7IxDa4lFB",
            "source": "MOCK_DOMAIN",
        }
    ]
    filtered = filter_source_by_domain(mock_lens_matched_images, "mock_domain")

    assert filtered[0]["title"] == "Manbusiness hi-res stock photography and images - Alamy from Alamy"
    assert filtered[1]["title"] == "Stock Photo: Smile, happy and motivation for business man, manager and leader alone in city, town or downtown. Portrait of excited corporate worker,  $30.00* from pixtastock.com"
    assert filtered[2]["title"] == "A Young Man In A Business Suit With A Blue Shirt And Red Tie On A City Street High-Res Stock Photo - Getty Images from Getty Images UK"
    assert filtered[3]["title"] == "Stock Illustration: attractive middle aged african american man on blue background. handsomeTV presenter in studio on popular channel. live stream  $30.00* from pixtastock.com"
    assert filtered[4]["title"] == "Portrait of handsome African businessman wearing suit and tie while smiling at rooftop park $5.00* from PhotoDune"
