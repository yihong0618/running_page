import React from "react";
import Layout from "../components/layout";

const Colophon = () => (
  <Layout>
    <h1 className="f-subheadline">Meta</h1>
    <div className="measure-wide">
      <p>
        This blog is a progressive web app, built using a modern
        Javascript-based static-site toolchain. Posts are written in Markdown
        with various extensions. The site is deployed on a content distribution
        network.
      </p>
      <p>
        It&rsquo;s{" "}
        <a
          className="link gray underline-hover"
          href="https://github.com/danpalmer/danpalmer.me"
        >
          open source
        </a>
        , and content is licenced under{" "}
        <a
          className="link gray underline-hover"
          href="https://creativecommons.org/licenses/by-sa/4.0/"
        >
          Creative Commons Attribution-ShareAlike 4.0 International License
        </a>
        .
      </p>
      <p>Affiliate links are used on this site.</p>
      <p>∞</p>
    </div>
  </Layout>
);

export default Colophon;
