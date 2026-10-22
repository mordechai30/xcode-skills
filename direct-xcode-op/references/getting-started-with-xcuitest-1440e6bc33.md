# Getting Started with XCUITest

XCUITest is a test automation framework used for UI testing of mobile apps and web applications on iOS devices such as iPads and iPhones. Let's discuss how to get started.

![Sauce Labs Author](<getting-started-with-xcuitest/fae2763828d14ecf69b8f59a.avif>)

Sauce Labs Author

October 7, 2022

[XCUITest](https://saucelabs.com/resources/topic-hub/xcuitest) is a test automation framework used for [UI testing](https://saucelabs.com/resources/blog/basics-of-automated-ui-testing) of mobile apps and web applications on iOS devices such as iPads and iPhones. It is part of Apple’s testing framework.

XCUITest was released in 2015 as part of the broader XCTest system built into XCode, Apple’s IDE (Integrated Developer Environment). Apple describes XCTest as a way to, “Create and run unit tests, performance tests, and UI tests for your Xcode project.”

XCUITest also provides a framework that allows developers to programmatically identify and interact with UI elements from other testing tools. XCUITest replaced the older UIAutomator technology and is the only supported UI interaction library for iOS as of 2022.


## What is UI Testing?

UI stands for “user interface” and refers to the forms, buttons, and other visual components your user interacts with.

To most users, your UI *is* your app. Most (if not all) interactions a user has with your app will be via the user interface, so any defects here will be readily apparent. Not only that, but defects from other parts of your app are often reflected in the UI. Because UI testing aims to ensure a positive end-user experience, it can be used to drive further, functional testing.


## Why is UI Testing Important?

[UI testing](https://saucelabs.com/products/visual-testing) is (or should be) a major part of the test regime for any user-oriented application. While it resembles code/unit testing in overall outline and approach, it differs from functional/code-oriented testing in some fairly specific ways. The goal of UI testing is not to look at the application's internal operation. It is, rather, to look at the application from the outside, and to test the application's response to user actions.

In this way, it is similar to [API testing](https://saucelabs.com/products/api-testing)—UI testing and API testing both focus on interface-based interactions with your app. In the case of UI testing, however, the interactions are not code-based API calls, but user actions by means of iOS device inputs.


### Basic UI test patterns

Most functional UI tests follow a basic pattern:

- Do something to the app by means of the UI. For an iOS-based app, this typically involves tapping, pressing, swiping, or other screen-based inputs.
- Record or capture the app's response. This can include both screen recording and capturing the state of internal application data.
- Measure the response against an expected response (by means of an assertion), then record or report the result.

A full UI test typically consists of a sequence of UI-based actions, with each following the above pattern.

Performance-based UI tests follow a somewhat different pattern:

- Do something via the UI - an action or sequence of actions.
- Record the time required to complete the action and expected response.
- Repeat the action or sequence a set number of times.
- Report the average completion time, plus outliers and other relevant statistics.


## XCUITest vs. Appium

[XCUITest](https://docs.saucelabs.com/mobile-apps/automated-testing/espresso-xcuitest/) and [Appium](https://docs.saucelabs.com/mobile-apps/automated-testing/appium/quickstart/) are both tools for automating real and virtual mobile devices, and both can be used as part of a robust test pipeline.

XCUITest is “closer to the metal” – that is, it’s more tightly integrated with iOS apps than Appium. This gives XCUITest a slight execution speed advantage over Appium, and makes for a simpler, iOS-only DevOps test toolchain. Because XCUITest is written by Apple, users are reliant on Apple for updates and features.

On the other hand, Appium is Open Source software. This gives Appium a large community of users providing updates, capabilities and features. Unlike XCUITest, Appium is not restricted to automation of iOS applications; it also supports Android and even Windows desktop applications. This makes Appium tooling and skills useful throughout the DevOps test toolchain, regardless of the device being developed for.


## XCUITest vs. Espresso

[Espresso](https://saucelabs.com/getting-started-with-espresso) is the testing framework that comes built into Android Studio, and is designed specifically for functional testing of Android applications.

Like XCUITest, [Espresso](https://docs.saucelabs.com/mobile-apps/automated-testing/espresso-xcuitest/) is popular among developers, as it is easy to set up, more stable than Appium, and gives them the ability to quickly test code components. With its automatic synchronization of UI, Espresso allows for faster test execution. It also brings faster feedback for developers, as it does not require a server for communication. The simplicity and convenience of this framework also stems from the fact that Android UI tests can be compiled into a separate APK, which allows for the test suites to run next to the app on the device.

Espresso also has the same lack of flexibility that we see with XCUITest. Firstly, Espresso is only compatible with Java and Kotlin, meaning that your tests can only be written in these languages. Additionally, Espresso can only be used to test Android apps, and so if your team is developing an app that will be listed on both iOS and Android, you will need to find another framework to help ensure compatibility across these different operating systems.


## Benefits of XCUITest


### XCode integration

XCUITest’s primary value comes from its close integration with XCode. With XCUITest, tests can be executed directly from XCode itself.  Your application and test code can be written in the same language (Objective-C or Swift), edited entirely within XCode, and stored in the same repository.

This makes writing unit, integration, and UI tests easier for your app developers.

Because XCUITest is so closely coupled with iOS, tests may execute faster compared with other solutions.


### Test recording

XCode offers the ability to “Record” tests; generating test code by watching interactions a user has with a connected Simulator or Real Device.  This recorded test code can then be tweaked to give a reliable, repeatable test, saving time during test creation.


### Flexible element identification

XCUITest allows testers to find elements by their title, label, value, or placeholder value.  XCUIElements can also have a unique ‘accessibility identifier’ specified for use in testing only, which can make finding elements fast and easy.

The ‘accessibility identifier’ is *not* related to the accessibility label read by tools such as Voice Over, however, Accessibility Testing is possible with XCUITest.


### Accessibility testing

Basic accessibility testing is possible in XCUITest by querying elements by their accessibility label and ensuring these labels make sense when read or heard.

There are also tools like [A11yUITests](https://github.com/rwapp/A11yUITests), which extend test cases to check for common accessibility issues.


## Drawbacks of XCUITest


### XCode (and thus macOS) is (almost) mandatory

XCode needs to be installed on every machine where your team runs XCUITest.  This includes tester machines and CI/CD environments.  Because XCode itself is macOS only, this can place significant budgetary and technical constraints on your operating environments, and limit your ability to use SAAS CI/CD solutions… with one exception.

The Sauce Labs Continuous Testing Library provides teams flexibility and scale when using XCUITest.  For more info, check out the “XCUITest and SauceCTL” section, below.


### Constrained framework/language choice

Because XCUITest is both the testing framework *and* the device interaction tool, it constrains your options for writing and running your tests.

For starters, XCUITest code can’t be written in Java, JavaScript, .Net, Python, or most other languages. In order to read, write and update tests, your team will need to use either Objective-C or Swift.

XCUITest code can’t be run separately from the XCUITest framework; You must run the tests using the XCUITest runner.

XCUITest may not be fully compatible with existing or planned digital confidence tooling.  For instance, while a 3rd party integration exists to allow you to use XCUITest with the popular Cucumber testing framework, it hasn’t been updated in over [four years](https://github.com/jerseysu/xcuitest_cucumberish) (as of July 2022).


### No Android support

XCUITest supports devices from one manufacturer: Apple. It’s not possible to use XCUITest for [Android app testing](https://saucelabs.com/getting-started-with-android-app-testing) on Android tablets, phones, or Wear devices. This may lead to teams having two completely separate test toolchains for iOS and Android.


## 5 XCUITest Best Practices

XCUITest includes the basic features needed to perform UI tests following the patterns described above. As is the case with all test suites, however, the value of the tests depends strongly on test design, implementation, and analysis—all of which are ultimately the responsibility of the testing team. Here are some best practices for UI testing in the context of the XCUITest framework:


### 1. UI Recording is your friend

UI recording is one of the most important built-in features of XCUITest. It allows you to record a test interaction with your app's UI, and save that interaction as test source code. You can then edit/tweak the code to add test details (including XCTest assertions), much like recording a macro for later editing and expansion. It may not be macho programming, but it saves time and trouble, and provides you with a reliable framework of generated code. The UI test recorder is also useful as an ongoing test tool. It provides information about interactions with the UI, including application internals.


### 2. Sequence-dependent or sequence-independent

Recognize that UI tests are generally sequence-dependent (a given test step may only be able to proceed if the previous step is successful), and write tests with this in mind. In your test code, self.continueAfterFailure will typically be set to NO to reflect this fact. If you are creating UI tests that are not sequence-dependent (for example, testing radio-button options which produce an immediate GUI response), you can set self.continueAfterFailure to YES, and make the appropriate provisions in the test code.


### 3. Test the full range of interactions

XCUITest allows you to set user interactions with considerable precision in most cases. You can, for example, specify tap(), doubleTap(), and twoFingerTap(); you can also set the number of taps. You can specify press() with a duration, and with both a duration and a dragging target. These interactions include four directional swipes (left, right, up, and down), pinch(), with scale and velocity, and rotate(), with velocity. Different users have different UI interaction styles; you can make full use of these features to develop a more detailed picture of the results of such varied interactions.


### 4. Don't forget accessibility

Along with standard UI testing, test handicapped/hearing-/visually impaired accessibility using the UIAccessibility protocol. In part, this is a matter of good sense and proactive customer service, since it maximizes your potential customer base. It may also turn out to be a practical necessity. Compliance with accessibility standards is becoming an increasingly common requirement for entry into many significant markets (including software for government use).


### 5. Go beyond standard functional and performance testing

Along with testing for errors and failed responses, test for unexpected or unwanted results which may not show up as errors. These could include accidental activation of unrelated features, actions that result in items being hidden or partially obscured, or other responses that interfere with the user experience. Remember: if an app works, but is too annoying to use, most people won't use it.


## Getting Started with XCUITest on Sauce Labs

The [saucectl](https://docs.saucelabs.com/dev/cli/saucectl/#installing-saucectl/) CLI allows teams to run [XCUITest](https://saucelabs.com/resources/topic-hub/xcuitest) on Windows, Linux and MacOS, at a greater scale than would be possible when running tests locally.

By utilizing Sauce Labs’ extensive [emulators](https://saucelabs.com/emulators-and-simulators) and [Real Device Cloud](https://saucelabs.com/products/mobile-testing/real-device-cloud), saucectl gives teams flexibility and easy scaling for their UI automation testing, along with the rich parallelization, test history filtering, and analytics of Sauce Labs.

Test code and the app under test are uploaded to a user’s choice of regional datacenter and run in serial or parallel. Test videos and screenshots are recorded and made available after tests, and results are reported “locally.”

This allows developers to run the same tests on their dev machine while making changes as they do at scale when deploying, saving time and ensuring high quality outcomes.

