Source: [https://developer.apple.com/documentation/xcode/changing-the-bundle-identifier](<https://developer.apple.com/documentation/xcode/changing-the-bundle-identifier>)

<a id="changing-the-bundle-identifier"></a>

# Changing the bundle identifier

Modify your app’s bundle identifier and update it anywhere it appears.

<a id="overview"></a>

## Overview

If you want to change your app’s bundle ID before you upload a build to App Store Connect, you need to change it in multiple locations. It’s particularly important that you update the bundle ID in all the locations below if your app uses certain capabilities that depend on the bundle ID.

The *bundle ID* is an information property list key that uniquely identifies your app throughout the system. Some capabilities use information property list or entitlement keys in your project that contain the main bundle ID.

When you choose a physical device other than a Mac to run your app, Xcode registers an App ID in your developer account based on the bundle ID in your developer account. If you aren’t a member of the Apple Developer Program, the number of App IDs you can register in Xcode is limited, so don’t change the bundle ID frequently. For more information, see [Running your app on simulated or physical devices](https://developer.apple.com/documentation/Xcode/running-your-app-on-simulated-or-physical-devices).

If you refer to a bundle ID in your code, replace it with the <doc://com.apple.documentation/documentation/Foundation/bundle()> macro that returns the bundle for the calling code.

> Note: If you use <doc://com.apple.Xcode/documentation/Xcode/Xcode-Cloud>, commit your project changes to your remote repository before creating a workflow.

<a id="change-the-main-bundle-id"></a>

## Change the main bundle ID

First, change the bundle ID in your Xcode project:

1. In the Project navigator, select the project.
2. In the project editor on the right, select the target.
3. Click the Signing & Capabilities tab and if necessary, expand Signing.
4. In the Bundle Identifier text field, enter your new bundle ID and press Return.

![An Xcode screenshot of the project editor showing the Signing & Capabilities tab selected with the Signing settings revealed and the cursor in the Bundle Identifier text field. ](<changing-the-bundle-identifier/9be81dbea3af716d6783af3a.png>)

Xcode changes the underlying <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/CFBundleIdentifier> information property list key that appears in the app bundle.

<a id="update-companion-target-bundle-ids"></a>

## Update companion target bundle IDs

Change any target bundle IDs that are derived from the main bundle ID, such as, bundle IDs for watchOS, app extension, and app clip targets.

In the project editor, select each target in the sidebar and update its bundle ID in the Bundle Identifier field on the Signing & Capabilities pane on the right.

For watchOS targets, Xcode updates the underlying <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/WKCompanionAppBundleIdentifier> and <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/WKAppBundleIdentifier> information property list keys.

<a id="change-keys-that-depend-on-the-main-bundle-id"></a>

## Change keys that depend on the main bundle ID

Update any other information property list and entitlement keys that contain the main bundle ID.

For example, if you use App Clips, change the associated <doc://com.apple.documentation/documentation/BundleResources/Entitlements/com.apple.developer.associated-appclip-app-identifiers> and <doc://com.apple.documentation/documentation/BundleResources/Entitlements/com.apple.developer.parent-application-identifiers> keys. If you have an app extension, be sure to change the <doc://com.apple.documentation/documentation/BundleResources/Entitlements/com.apple.developer.app-migration.data-container-access> key too.

<a id="update-the-bundle-id-in-app-store-connect"></a>

## Update the bundle ID in App Store Connect

> Important: If you previously uploaded a build to App Store Connect, you can’t change the bundle ID. Create a new app record with the bundle ID instead of updating the existing app record. For more information, see [Add a new app](https://developer.apple.com/help/app-store-connect/create-an-app-record/add-a-new-app).

If you plan to distribute your app through the App Store and you’ve created an app record, but haven’t uploaded a build yet, then you can still change the bundle ID in your app record to match your Xcode project. After you change the bundle ID in your Xcode project, to update the bundle ID in your app record in App Store Connect:

1. Build and run your app on a device to register the new bundle ID and update the provisioning profile.
2. In App Store Connect, select Apps and then select your app.
3. In the Distribution pane, select App Information under General in the sidebar.
4. Choose the new identifier from the Bundle ID pop-up menu under General Information on the right, and click Save.

For more information, see [View and edit app information](https://developer.apple.com/help/app-store-connect/create-an-app-record/view-and-edit-app-information).

Update any other settings in App Store Connect that use the bundle ID, such as in-app purchase settings. Re-request any special entitlements from Apple that require approval. Deleting an existing app record doesn’t make its bundle ID available.

> Note: If you use any third-party services that depend on your app’s bundle ID, notify them to update your app’s bundle ID too.

<a id="update-manual-provisioning-profiles"></a>

## Update manual provisioning profiles

If you use manual provisioning, update the App ID in those provisioning files to match the bundle ID in your project. For more information, see [Edit, download, or delete provisioning profiles](https://developer.apple.com/help/account/provisioning-profiles/edit-download-or-delete-profiles) in Developer Account Help. After you update your provisioning profile in your developer account, you can download it from Xcode > Settings > Apple Accounts, using the Download Manual Profiles button when you select your account.

If you toggle the “Automatically manage signing” checkbox in the Signing & Capabilities pane, Xcode updates your provisioning profiles for you.

---

Copyright © 2026 Apple Inc. All rights reserved. | [Terms of Use](https://www.apple.com/legal/internet-services/terms/site.html) | [Privacy Policy](https://www.apple.com/privacy/privacy-policy)
